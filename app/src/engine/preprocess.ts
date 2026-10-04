// Copied unchanged from kb/engine-cowork/parity/src/preprocess.ts (bit-exact with app/ml/train.py eval_transform; see PARITY.md).
/**
 * preprocess.ts: pure TypeScript (no DOM) copy of the Jani eval transform.
 *
 * Reproduces, for an RGB image decoded at native resolution:
 *   torchvision Compose([Resize(224), CenterCrop(224), ToTensor(),
 *                        Normalize(IMAGENET_MEAN, IMAGENET_STD)])
 * applied to a PIL image, which means Pillow's BILINEAR resampler
 * (separable, antialiased, 8-bit fixed point, horizontal pass first).
 *
 * Input:  RGBA bytes as returned by getImageData (alpha is ignored).
 * Output: Float32Array NCHW [1, 3, size, size].
 *
 * Verified bit-exact against torchvision 0.29.1 + Pillow 12.3.0 on 49 images (see PARITY.md).
 */

export const INPUT_SIZE = 224;
export const IMAGENET_MEAN: readonly number[] = [0.485, 0.456, 0.406];
export const IMAGENET_STD: readonly number[] = [0.229, 0.224, 0.225];

/** Pillow Resample.c: PRECISION_BITS = 32 - 8 - 2. */
const PRECISION_BITS = 22;
const ONE = 1 << PRECISION_BITS; // 4194304
const HALF = 1 << (PRECISION_BITS - 1); // 2097152

export type Pixels = Uint8ClampedArray | Uint8Array;

export interface PreprocessOptions {
  /** Output side. Default 224. */
  size?: number;
  mean?: readonly number[];
  std?: readonly number[];
  /**
   * Optional speed path for very large inputs. When true, the image is first
   * box-reduced by an integer factor so that it stays at least 2x the resize
   * target (the same idea as Pillow's reducing_gap=2.0), then the exact
   * bilinear pass runs. Not bit-exact with the training transform; the extra
   * drift is measured in PARITY.md. Default false (exact).
   */
  fastPath?: boolean;
}

/** torchvision _compute_resized_output_size for Resize(int). Returns [w, h]. */
export function resizedSize(w: number, h: number, size = INPUT_SIZE): [number, number] {
  const short = w <= h ? w : h;
  const long = w <= h ? h : w;
  // Python: int(requested_new_short * long / short), float64 division then truncation.
  const newLong = Math.trunc((size * long) / short);
  return w <= h ? [size, newLong] : [newLong, size];
}

/** Python 3 round() on a float: round half to even. */
export function roundHalfEven(x: number): number {
  const f = Math.floor(x);
  const d = x - f;
  if (d > 0.5) return f + 1;
  if (d < 0.5) return f;
  return f % 2 === 0 ? f : f + 1;
}

/** torchvision center_crop offsets for an image already at least `size` on both sides. */
export function centerCropOffsets(w: number, h: number, size = INPUT_SIZE): { left: number; top: number } {
  if (w < size || h < size) throw new Error(`center crop needs padding: ${w}x${h}`);
  return {
    top: roundHalfEven((h - size) / 2.0),
    left: roundHalfEven((w - size) / 2.0),
  };
}

export interface Coeffs {
  ksize: number;
  /** Per output index: [first source index, tap count]. */
  bounds: Int32Array;
  /** Fixed-point weights, ksize per output index. */
  kk: Int32Array;
}

/**
 * Pillow precompute_coeffs() + normalize_coeffs_8bpc() for the BILINEAR
 * (triangle, support 1) filter, for output indices [outStart, outStart+outCount).
 * in0/in1 are the source box edges (Pillow keeps them as float32).
 */
export function precomputeCoeffs(
  inSize: number,
  in0: number,
  in1: number,
  outSize: number,
  outStart = 0,
  outCount = outSize,
): Coeffs {
  const f0 = Math.fround(in0);
  const f1 = Math.fround(in1);
  const scale = Math.fround(f1 - f0) / outSize; // (double)(in1 - in0) / outSize
  const filterscale = scale < 1.0 ? 1.0 : scale;
  const support = 1.0 * filterscale; // BILINEAR support = 1.0
  const ksize = Math.ceil(support) * 2 + 1;
  const ss = 1.0 / filterscale;
  const bounds = new Int32Array(outCount * 2);
  const kk = new Int32Array(outCount * ksize);
  const k = new Float64Array(ksize);
  for (let i = 0; i < outCount; i++) {
    const xx = outStart + i;
    const center = f0 + (xx + 0.5) * scale;
    let ww = 0.0;
    let xmin = Math.trunc(center - support + 0.5); // C (int) cast
    if (xmin < 0) xmin = 0;
    let xmax = Math.trunc(center + support + 0.5);
    if (xmax > inSize) xmax = inSize;
    xmax -= xmin;
    for (let x = 0; x < xmax; x++) {
      let t = (x + xmin - center + 0.5) * ss;
      if (t < 0.0) t = -t;
      const w = t < 1.0 ? 1.0 - t : 0.0;
      k[x] = w;
      ww += w;
    }
    const base = i * ksize;
    for (let x = 0; x < xmax; x++) {
      const v = ww !== 0.0 ? k[x] / ww : k[x];
      kk[base + x] = v < 0 ? Math.trunc(-0.5 + v * ONE) : Math.trunc(0.5 + v * ONE);
    }
    bounds[i * 2] = xmin;
    bounds[i * 2 + 1] = xmax;
  }
  return { ksize, bounds, kk };
}

function clip8(s: number): number {
  const v = s >> PRECISION_BITS; // arithmetic shift, as in C
  return v < 0 ? 0 : v > 255 ? 255 : v;
}

/**
 * Pillow ImagingResample (BILINEAR, 8 bpc) restricted to an output window.
 * src: interleaved pixels with `srcChannels` bytes per pixel (3 or 4); the
 * first 3 channels are resampled. Returns interleaved RGB (3 bytes/pixel) of
 * size cw x ch for output columns [cx, cx+cw) and rows [cy, cy+ch) of the
 * full outW x outH resize. Values equal the full resize followed by a crop.
 */
export function resizeWindow(
  src: Pixels,
  srcW: number,
  srcH: number,
  srcChannels: number,
  outW: number,
  outH: number,
  cx: number,
  cy: number,
  cw: number,
  ch: number,
  box: readonly number[] = [0, 0, srcW, srcH],
): Uint8Array {
  const bx0 = Math.fround(box[0]);
  const by0 = Math.fround(box[1]);
  const bx1 = Math.fround(box[2]);
  const by1 = Math.fround(box[3]);
  const needH = outW !== srcW || bx0 !== 0 || bx1 !== outW;
  const needV = outH !== srcH || by0 !== 0 || by1 !== outH;

  // Vertical coefficients decide which source rows the horizontal pass needs.
  const vc = precomputeCoeffs(srcH, by0, by1, outH, cy, ch);
  let rowFirst: number;
  let rowLast: number; // exclusive
  if (needV) {
    rowFirst = vc.bounds[0];
    rowLast = vc.bounds[(ch - 1) * 2] + vc.bounds[(ch - 1) * 2 + 1];
    for (let i = 0; i < ch; i++) {
      // bounds are monotonic for this filter, but stay safe
      if (vc.bounds[i * 2] < rowFirst) rowFirst = vc.bounds[i * 2];
      const e = vc.bounds[i * 2] + vc.bounds[i * 2 + 1];
      if (e > rowLast) rowLast = e;
    }
  } else {
    rowFirst = cy;
    rowLast = cy + ch;
  }
  const rows = rowLast - rowFirst;

  // Horizontal pass into an 8-bit intermediate (rows x cw x 3).
  const tmp = new Uint8Array(rows * cw * 3);
  if (needH) {
    const hc = precomputeCoeffs(srcW, bx0, bx1, outW, cx, cw);
    const { ksize, bounds, kk } = hc;
    for (let r = 0; r < rows; r++) {
      const rowOff = (rowFirst + r) * srcW * srcChannels;
      let o = r * cw * 3;
      for (let i = 0; i < cw; i++) {
        const xmin = bounds[i * 2];
        const n = bounds[i * 2 + 1];
        const kb = i * ksize;
        let s0 = HALF;
        let s1 = HALF;
        let s2 = HALF;
        let p = rowOff + xmin * srcChannels;
        for (let x = 0; x < n; x++) {
          const w = kk[kb + x];
          s0 += src[p] * w;
          s1 += src[p + 1] * w;
          s2 += src[p + 2] * w;
          p += srcChannels;
        }
        tmp[o++] = clip8(s0);
        tmp[o++] = clip8(s1);
        tmp[o++] = clip8(s2);
      }
    }
  } else {
    for (let r = 0; r < rows; r++) {
      const rowOff = (rowFirst + r) * srcW * srcChannels;
      let o = r * cw * 3;
      for (let i = 0; i < cw; i++) {
        const p = rowOff + (cx + i) * srcChannels;
        tmp[o++] = src[p];
        tmp[o++] = src[p + 1];
        tmp[o++] = src[p + 2];
      }
    }
  }

  if (!needV) return tmp; // rows == ch, already the window

  // Vertical pass from the intermediate.
  const out = new Uint8Array(ch * cw * 3);
  const { ksize, bounds, kk } = vc;
  const stride = cw * 3;
  for (let j = 0; j < ch; j++) {
    const ymin = bounds[j * 2] - rowFirst;
    const n = bounds[j * 2 + 1];
    const kb = j * ksize;
    let o = j * stride;
    for (let i = 0; i < stride; i++) {
      let s = HALF;
      let p = ymin * stride + i;
      for (let y = 0; y < n; y++) {
        s += tmp[p] * kk[kb + y];
        p += stride;
      }
      out[o++] = clip8(s);
    }
  }
  return out;
}

/**
 * Integer box reduce (fast path only). Same arithmetic as Pillow ImagingReduce
 * for the full blocks: (sum + n/2) * trunc(2^32 / (256 n)) >> 24; partial
 * blocks at the right and bottom edges average the pixels they contain.
 * Returns RGB interleaved, size ceil(w/fx) x ceil(h/fy).
 */
export function boxReduce(
  src: Pixels,
  w: number,
  h: number,
  channels: number,
  fx: number,
  fy: number,
): { data: Uint8Array; w: number; h: number } {
  const ow = Math.ceil(w / fx);
  const oh = Math.ceil(h / fy);
  const out = new Uint8Array(ow * oh * 3);
  const multCache = new Map<number, number>();
  const mult = (n: number): number => {
    let m = multCache.get(n);
    if (m === undefined) {
      m = Math.trunc(Math.fround(4294967296 / Math.fround(256 * n)));
      multCache.set(n, m);
    }
    return m;
  };
  for (let oy = 0; oy < oh; oy++) {
    const y0 = oy * fy;
    const y1 = Math.min(y0 + fy, h);
    for (let ox = 0; ox < ow; ox++) {
      const x0 = ox * fx;
      const x1 = Math.min(x0 + fx, w);
      const n = (y1 - y0) * (x1 - x0);
      const amend = Math.floor(n / 2);
      let s0 = amend;
      let s1 = amend;
      let s2 = amend;
      for (let y = y0; y < y1; y++) {
        let p = (y * w + x0) * channels;
        for (let x = x0; x < x1; x++) {
          s0 += src[p];
          s1 += src[p + 1];
          s2 += src[p + 2];
          p += channels;
        }
      }
      const m = mult(n);
      const o = (oy * ow + ox) * 3;
      out[o] = Math.floor((s0 * m) / 16777216);
      out[o + 1] = Math.floor((s1 * m) / 16777216);
      out[o + 2] = Math.floor((s2 * m) / 16777216);
    }
  }
  return { data: out, w: ow, h: oh };
}

/** Float32 lookup table: torchvision ToTensor (u8 / 255) then Normalize, in float32. */
export function buildNormLut(mean: readonly number[], std: readonly number[]): Float32Array {
  const lut = new Float32Array(3 * 256);
  for (let c = 0; c < 3; c++) {
    const m = Math.fround(mean[c]);
    const s = Math.fround(std[c]);
    for (let u = 0; u < 256; u++) {
      const x = Math.fround(u / 255);
      lut[c * 256 + u] = Math.fround(Math.fround(x - m) / s);
    }
  }
  return lut;
}

const lutCache = new Map<string, Float32Array>();

/**
 * Resize(size) + CenterCrop(size) as uint8 RGB interleaved (size x size x 3).
 * Exposed for tests and debugging.
 */
export function resizeAndCrop(
  rgba: Pixels,
  width: number,
  height: number,
  opts: PreprocessOptions = {},
  channels = 4,
): Uint8Array {
  const size = opts.size ?? INPUT_SIZE;
  if (rgba.length < width * height * channels) throw new Error("pixel buffer too small");
  const [nw, nh] = resizedSize(width, height, size);
  const { left, top } = centerCropOffsets(nw, nh, size);

  if (opts.fastPath) {
    // reducing_gap = 2.0: factor = int(in / out / 2) or 1, per axis.
    const fx = Math.trunc(width / nw / 2.0) || 1;
    const fy = Math.trunc(height / nh / 2.0) || 1;
    if (fx > 1 || fy > 1) {
      const red = boxReduce(rgba, width, height, channels, fx, fy);
      const box = [0, 0, width / fx, height / fy];
      return resizeWindow(red.data, red.w, red.h, 3, nw, nh, left, top, size, size, box);
    }
  }
  if (nw === width && nh === height) {
    // torchvision returns the PIL image unchanged when the size already matches.
    const out = new Uint8Array(size * size * 3);
    let o = 0;
    for (let y = 0; y < size; y++) {
      let p = ((top + y) * width + left) * channels;
      for (let x = 0; x < size; x++) {
        out[o++] = rgba[p];
        out[o++] = rgba[p + 1];
        out[o++] = rgba[p + 2];
        p += channels;
      }
    }
    return out;
  }
  return resizeWindow(rgba, width, height, channels, nw, nh, left, top, size, size);
}

/**
 * Full eval transform. rgba: getImageData().data of the decoded image at
 * native resolution. Returns Float32Array NCHW [1, 3, size, size].
 */
export function preprocess(
  rgba: Pixels,
  width: number,
  height: number,
  opts: PreprocessOptions = {},
): Float32Array {
  const size = opts.size ?? INPUT_SIZE;
  const mean = opts.mean ?? IMAGENET_MEAN;
  const std = opts.std ?? IMAGENET_STD;
  const key = mean.join(",") + "|" + std.join(",");
  let lut = lutCache.get(key);
  if (!lut) {
    lut = buildNormLut(mean, std);
    lutCache.set(key, lut);
  }
  const rgb = resizeAndCrop(rgba, width, height, opts, 4);
  const plane = size * size;
  const out = new Float32Array(3 * plane);
  for (let i = 0, p = 0; i < plane; i++, p += 3) {
    out[i] = lut[rgb[p]];
    out[plane + i] = lut[256 + rgb[p + 1]];
    out[2 * plane + i] = lut[512 + rgb[p + 2]];
  }
  return out;
}

/** Softmax of logits / T (float64), as in export.py write_parity_samples. */
export function softmaxT(logits: ArrayLike<number>, T = 1): number[] {
  let mx = -Infinity;
  for (let i = 0; i < logits.length; i++) mx = Math.max(mx, logits[i] / T);
  const e: number[] = [];
  let sum = 0;
  for (let i = 0; i < logits.length; i++) {
    const v = Math.exp(logits[i] / T - mx);
    e.push(v);
    sum += v;
  }
  return e.map((v) => v / sum);
}

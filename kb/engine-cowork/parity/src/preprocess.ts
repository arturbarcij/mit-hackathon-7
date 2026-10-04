/**
 * preprocess.ts
 *
 * Pure TypeScript reproduction of the Jani eval transform from app/ml/train.py:
 *
 *   transforms.Resize(224)        PIL bilinear, shorter side to 224, antialias
 *   transforms.CenterCrop(224)
 *   transforms.ToTensor()         uint8 / 255 as float32
 *   transforms.Normalize(mean, std)
 *
 * The resize follows Pillow's libImaging/Resample.c (8 bit path) step by step:
 *   - triangle filter, support 1.0, scaled by the downscale factor (antialias)
 *   - coefficients normalised to sum 1, then quantised to 22 bit fixed point
 *   - horizontal pass, round to 8 bit, then vertical pass, round to 8 bit
 * This is what torchvision does when it is given a PIL image, so the tensor
 * produced here matches the Python tensor bit for bit for lossless inputs.
 *
 * No DOM dependency. Works in Node and in a browser or worker.
 * Browser glue (File / ImageBitmap to RGBA) lives in preprocess-browser.ts.
 */

export interface RawImage {
  /** RGBA (4 bytes per pixel) or RGB (3 bytes per pixel), row major, top left first. */
  data: Uint8ClampedArray | Uint8Array;
  width: number;
  height: number;
}

export interface PreprocessSpec {
  size: number;
  resize: 'shorter_side_then_center_crop';
  mean: [number, number, number];
  std: [number, number, number];
  layout: 'NCHW';
  range: '0-1';
}

/** Matches model.json "input" as written by app/ml/export.py. */
export const DEFAULT_SPEC: PreprocessSpec = {
  size: 224,
  resize: 'shorter_side_then_center_crop',
  mean: [0.485, 0.456, 0.406],
  std: [0.229, 0.224, 0.225],
  layout: 'NCHW',
  range: '0-1',
};

export interface PreprocessResult {
  /** Float32 NCHW tensor, length 1 * 3 * size * size. */
  tensor: Float32Array;
  dims: [number, number, number, number];
  /** Intermediate 8 bit RGB after resize and crop (size * size * 3). Useful for debugging. */
  rgb: Uint8Array;
  /** Size the image was resized to before cropping. */
  resized: { width: number; height: number };
  crop: { left: number; top: number };
}

const PRECISION_BITS = 32 - 8 - 2; // 22, as in Pillow
const PRECISION_ONE = 1 << PRECISION_BITS;
const PRECISION_HALF = 1 << (PRECISION_BITS - 1);
const CLIP_MAX = PRECISION_ONE * 256;

/** Pillow bilinear_filter. */
function bilinear(x: number): number {
  x = Math.abs(x);
  return x < 1.0 ? 1.0 - x : 0.0;
}

/**
 * Pillow precompute_coeffs for one axis, followed by normalize_coeffs_8bpc.
 * Returns integer coefficients (22 bit fixed point) and bounds per output index.
 */
function precomputeCoeffs(inSize: number, outSize: number): { bounds: Int32Array; kk: Int32Array; ksize: number } {
  const support0 = 1.0; // bilinear
  const scale = inSize / outSize;
  const filterscale = scale < 1.0 ? 1.0 : scale;
  const support = support0 * filterscale;
  const ksize = Math.ceil(support) * 2 + 1;
  const bounds = new Int32Array(outSize * 2);
  const prekk = new Float64Array(outSize * ksize);
  const ss = 1.0 / filterscale;
  for (let xx = 0; xx < outSize; xx++) {
    const center = (xx + 0.5) * scale;
    let xmin = Math.trunc(center - support + 0.5);
    if (xmin < 0) xmin = 0;
    let xmax = Math.trunc(center + support + 0.5);
    if (xmax > inSize) xmax = inSize;
    xmax -= xmin;
    let ww = 0.0;
    const base = xx * ksize;
    let x = 0;
    for (; x < xmax; x++) {
      const w = bilinear((x + xmin - center + 0.5) * ss);
      prekk[base + x] = w;
      ww += w;
    }
    for (x = 0; x < xmax; x++) {
      if (ww !== 0.0) prekk[base + x] /= ww;
    }
    for (; x < ksize; x++) prekk[base + x] = 0;
    bounds[xx * 2] = xmin;
    bounds[xx * 2 + 1] = xmax;
  }
  // normalize_coeffs_8bpc: round to int with 22 fractional bits (C cast truncates toward zero)
  const kk = new Int32Array(outSize * ksize);
  for (let i = 0; i < kk.length; i++) {
    const v = prekk[i];
    kk[i] = v < 0 ? Math.trunc(-0.5 + v * PRECISION_ONE) : Math.trunc(0.5 + v * PRECISION_ONE);
  }
  return { bounds, kk, ksize };
}

/** Pillow clip8: (in >> 22) clamped to 0..255. */
function clip8(v: number): number {
  if (v >= CLIP_MAX) return 255;
  if (v <= 0) return 0;
  return Math.floor(v / PRECISION_ONE); // arithmetic shift on a positive int
}

/**
 * Resize a packed RGB buffer with Pillow's bilinear antialiased resample.
 * Horizontal pass first, then vertical, each rounded to 8 bit, like ImagingResampleInner.
 */
export function resizeBilinearPIL(src: Uint8Array, w: number, h: number, outW: number, outH: number): Uint8Array {
  let cur = src;
  let curW = w;
  let curH = h;
  if (outW !== w) {
    const { bounds, kk, ksize } = precomputeCoeffs(w, outW);
    const out = new Uint8Array(outW * h * 3);
    for (let yy = 0; yy < h; yy++) {
      const rowIn = yy * w * 3;
      const rowOut = yy * outW * 3;
      for (let xx = 0; xx < outW; xx++) {
        const xmin = bounds[xx * 2];
        const xmax = bounds[xx * 2 + 1];
        const kb = xx * ksize;
        let s0 = PRECISION_HALF;
        let s1 = PRECISION_HALF;
        let s2 = PRECISION_HALF;
        for (let x = 0; x < xmax; x++) {
          const k = kk[kb + x];
          const p = rowIn + (x + xmin) * 3;
          s0 += cur[p] * k;
          s1 += cur[p + 1] * k;
          s2 += cur[p + 2] * k;
        }
        const o = rowOut + xx * 3;
        out[o] = clip8(s0);
        out[o + 1] = clip8(s1);
        out[o + 2] = clip8(s2);
      }
    }
    cur = out;
    curW = outW;
  }
  if (outH !== h) {
    const { bounds, kk, ksize } = precomputeCoeffs(h, outH);
    const out = new Uint8Array(curW * outH * 3);
    for (let yy = 0; yy < outH; yy++) {
      const ymin = bounds[yy * 2];
      const ymax = bounds[yy * 2 + 1];
      const kb = yy * ksize;
      const rowOut = yy * curW * 3;
      for (let xx = 0; xx < curW; xx++) {
        let s0 = PRECISION_HALF;
        let s1 = PRECISION_HALF;
        let s2 = PRECISION_HALF;
        for (let y = 0; y < ymax; y++) {
          const k = kk[kb + y];
          const p = ((y + ymin) * curW + xx) * 3;
          s0 += cur[p] * k;
          s1 += cur[p + 1] * k;
          s2 += cur[p + 2] * k;
        }
        const o = rowOut + xx * 3;
        out[o] = clip8(s0);
        out[o + 1] = clip8(s1);
        out[o + 2] = clip8(s2);
      }
    }
    cur = out;
    curH = outH;
  }
  return cur;
}

/**
 * torchvision _compute_resized_output_size for an int size:
 * short side becomes `size`, long side = int(size * long / short).
 */
export function resizedSize(w: number, h: number, size: number): { width: number; height: number } {
  const short = Math.min(w, h);
  const long = Math.max(w, h);
  const newShort = size;
  const newLong = Math.trunc((size * long) / short);
  return w <= h ? { width: newShort, height: newLong } : { width: newLong, height: newShort };
}

/** Python round() is round half to even. (x - c) / 2 is always an integer or .5. */
function roundHalfEven(v: number): number {
  const f = Math.floor(v);
  const diff = v - f;
  if (diff < 0.5) return f;
  if (diff > 0.5) return f + 1;
  return f % 2 === 0 ? f : f + 1;
}

/** Convert RGBA or RGB input to a packed RGB Uint8Array. */
export function toRGB(img: RawImage): Uint8Array {
  const n = img.width * img.height;
  if (img.data.length === n * 3) {
    return img.data instanceof Uint8Array ? img.data : new Uint8Array(img.data.buffer, img.data.byteOffset, n * 3);
  }
  if (img.data.length !== n * 4) {
    throw new Error(`RawImage data length ${img.data.length} does not match ${img.width}x${img.height} RGB or RGBA`);
  }
  const out = new Uint8Array(n * 3);
  const d = img.data;
  for (let i = 0, j = 0; i < n; i++, j += 4) {
    out[i * 3] = d[j];
    out[i * 3 + 1] = d[j + 1];
    out[i * 3 + 2] = d[j + 2];
  }
  return out;
}

/** Build the 256 entry lookup for one channel, emulating float32 ToTensor + Normalize. */
function buildLUT(mean: number, std: number): Float32Array {
  const m = Math.fround(mean);
  const s = Math.fround(std);
  const lut = new Float32Array(256);
  for (let v = 0; v < 256; v++) {
    // torch: (uint8 -> float32) / 255, then sub_(mean), then div_(std), all in float32.
    const t = Math.fround(v / 255);
    lut[v] = Math.fround(Math.fround(t - m) / s);
  }
  return lut;
}

/**
 * Full eval transform. Returns the NCHW float32 tensor and the intermediate 8 bit crop.
 */
export function preprocess(img: RawImage, spec: PreprocessSpec = DEFAULT_SPEC): PreprocessResult {
  if (spec.resize !== 'shorter_side_then_center_crop' || spec.layout !== 'NCHW' || spec.range !== '0-1') {
    throw new Error(`Unsupported preprocess spec: ${JSON.stringify(spec)}`);
  }
  const size = spec.size;
  const rgb = toRGB(img);
  let w = img.width;
  let h = img.height;

  // Resize: torchvision returns the image unchanged when the computed size equals the input size.
  const target = resizedSize(w, h, size);
  let cur = rgb;
  if (target.width !== w || target.height !== h) {
    cur = resizeBilinearPIL(rgb, w, h, target.width, target.height);
    w = target.width;
    h = target.height;
  }

  // CenterCrop(size). After the resize both sides are >= size, so no padding path is needed.
  const top = roundHalfEven((h - size) / 2.0);
  const left = roundHalfEven((w - size) / 2.0);
  if (top < 0 || left < 0) {
    throw new Error(`Image ${w}x${h} smaller than crop ${size}; padding path not implemented`);
  }
  const crop = new Uint8Array(size * size * 3);
  for (let y = 0; y < size; y++) {
    const srcOff = ((top + y) * w + left) * 3;
    crop.set(cur.subarray(srcOff, srcOff + size * 3), y * size * 3);
  }

  // ToTensor + Normalize, NCHW.
  const luts = [buildLUT(spec.mean[0], spec.std[0]), buildLUT(spec.mean[1], spec.std[1]), buildLUT(spec.mean[2], spec.std[2])];
  const plane = size * size;
  const tensor = new Float32Array(3 * plane);
  for (let i = 0; i < plane; i++) {
    tensor[i] = luts[0][crop[i * 3]];
    tensor[plane + i] = luts[1][crop[i * 3 + 1]];
    tensor[2 * plane + i] = luts[2][crop[i * 3 + 2]];
  }
  return { tensor, dims: [1, 3, size, size], rgb: crop, resized: target, crop: { left, top } };
}

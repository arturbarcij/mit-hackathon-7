// Image-validity gate: one leaf flat on a plain page. Port of kb/edge/sheet_gate.py.
// A photo passes only if:
//   - at least 30% of pixels look like plain paper (bright, low saturation),
//   - the leaf does not run off the frame (at most 15% of the outer 6% band is leaf),
//   - the leaf covers at least 8% of the image.
// A failing photo gets the retake card 'retake_on_page', never a diagnosis.
// Thresholds: set by the lead on Sat 3 Oct night on the same images field_check.py scores
// (in-sample until fresh phone photos confirm them, EDGE_PLAN move 2).
// Pure: no DOM, no canvas. Works on RGBA bytes of any size; shrinks to at most 256 px first,
// with the same output size as PIL Image.thumbnail((256, 256)).

export const GATE_SIDE = 256;
export const PAPER_MIN = 0.3;
export const EDGE_TOUCH_MAX = 0.15;
export const LEAF_MIN = 0.08;

export type GateDetail = 'no_page' | 'leaf_cut_off' | 'leaf_too_small';

export interface GateResult {
  ok: boolean;
  reason?: 'not_on_page';
  /** Which test failed first (same order and names as sheet_gate.py). */
  detail?: GateDetail;
  /** Fraction of pixels that look like paper, 3 decimals. */
  paper: number;
  /** Fraction of the outer band that is leaf, 3 decimals. */
  edge: number;
  /** Fraction of pixels that are leaf, 3 decimals. */
  leaf: number;
}

/** Output size of PIL Image.thumbnail((side, side)): keeps aspect, never enlarges. */
export function thumbnailSize(w: number, h: number, side = GATE_SIDE): { width: number; height: number } {
  if (w <= side && h <= side) return { width: w, height: h };
  const aspect = w / h;
  let x = side;
  let y = side;
  // Same choice as Pillow's preserve_aspect_ratio: floor or ceil, whichever keeps the aspect closer.
  const roundAspect = (n: number, key: (v: number) => number) => {
    const lo = Math.floor(n);
    const hi = Math.ceil(n);
    return Math.max(key(lo) <= key(hi) ? lo : hi, 1);
  };
  if (x / y >= aspect) x = roundAspect(y * aspect, (n) => Math.abs(aspect - n / y));
  else y = roundAspect(x / aspect, (n) => (n === 0 ? 0 : Math.abs(aspect - x / n)));
  return { width: x, height: y };
}

/** Area-average downscale of RGB(A) bytes to outW x outH. Returns RGB floats 0 to 1. */
export function areaDownscale(rgba: ArrayLike<number>, w: number, h: number, outW: number, outH: number): Float32Array {
  const out = new Float32Array(outW * outH * 3);
  if (outW === w && outH === h) {
    for (let i = 0; i < w * h; i++) {
      out[i * 3] = rgba[i * 4] / 255;
      out[i * 3 + 1] = rgba[i * 4 + 1] / 255;
      out[i * 3 + 2] = rgba[i * 4 + 2] / 255;
    }
    return out;
  }
  const sx = w / outW;
  const sy = h / outH;
  for (let oy = 0; oy < outH; oy++) {
    const y0 = oy * sy;
    const y1 = y0 + sy;
    for (let ox = 0; ox < outW; ox++) {
      const x0 = ox * sx;
      const x1 = x0 + sx;
      let r = 0;
      let g = 0;
      let b = 0;
      let wsum = 0;
      for (let y = Math.floor(y0); y < Math.min(h, Math.ceil(y1)); y++) {
        const wy = Math.min(y + 1, y1) - Math.max(y, y0);
        if (wy <= 0) continue;
        for (let x = Math.floor(x0); x < Math.min(w, Math.ceil(x1)); x++) {
          const wx = Math.min(x + 1, x1) - Math.max(x, x0);
          if (wx <= 0) continue;
          const wgt = wx * wy;
          const i = (y * w + x) * 4;
          r += rgba[i] * wgt;
          g += rgba[i + 1] * wgt;
          b += rgba[i + 2] * wgt;
          wsum += wgt;
        }
      }
      const o = (oy * outW + ox) * 3;
      out[o] = r / wsum / 255;
      out[o + 1] = g / wsum / 255;
      out[o + 2] = b / wsum / 255;
    }
  }
  return out;
}

const r3 = (v: number) => Math.round(v * 1000) / 1000;

/** The gate on RGBA bytes (alpha ignored). Never throws; an empty image fails as 'no_page'. */
export function sheetGate(rgba: ArrayLike<number>, w: number, h: number): GateResult {
  if (!(w > 0 && h > 0) || !rgba || rgba.length < w * h * 4) {
    return { ok: false, reason: 'not_on_page', detail: 'no_page', paper: 0, edge: 0, leaf: 0 };
  }
  const { width: tw, height: th } = thumbnailSize(w, h);
  const rgb = areaDownscale(rgba, w, h, tw, th);
  const b = Math.max(2, Math.floor(0.06 * Math.min(tw, th)));
  let paperN = 0;
  let leafN = 0;
  let borderN = 0;
  let borderLeafN = 0;
  for (let y = 0; y < th; y++) {
    const yBorder = y < b || y >= th - b;
    for (let x = 0; x < tw; x++) {
      const i = (y * tw + x) * 3;
      const r = rgb[i];
      const g = rgb[i + 1];
      const bl = rgb[i + 2];
      const mx = Math.max(r, g, bl);
      const mn = Math.min(r, g, bl);
      const sat = (mx - mn) / (mx + 1e-6);
      const paper = mx > 0.45 && sat < 0.18;
      const leaf = sat > 0.22 && !paper;
      if (paper) paperN++;
      if (leaf) leafN++;
      if (yBorder || x < b || x >= tw - b) {
        borderN++;
        if (leaf) borderLeafN++;
      }
    }
  }
  const total = tw * th;
  const paper = paperN / total;
  const edge = borderN > 0 ? borderLeafN / borderN : 0;
  const leaf = leafN / total;
  const ok = paper >= PAPER_MIN && edge <= EDGE_TOUCH_MAX && leaf >= LEAF_MIN;
  const res: GateResult = { ok, paper: r3(paper), edge: r3(edge), leaf: r3(leaf) };
  if (!ok) {
    res.reason = 'not_on_page';
    res.detail = paper < PAPER_MIN ? 'no_page' : edge > EDGE_TOUCH_MAX ? 'leaf_cut_off' : 'leaf_too_small';
  }
  return res;
}

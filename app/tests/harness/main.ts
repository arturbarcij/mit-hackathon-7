import * as engine from '../../src/engine';
import { inferProbsForTest } from '../../src/engine/model';

type Rgb = [number, number, number];

/** Textured test photo: a base colour with random 8 px blocks, so it passes the blur check. */
async function makeLeafFile(name: string, base: Rgb, opts: { width?: number; height?: number; texture?: number } = {}): Promise<File> {
  const w = opts.width ?? 1200;
  const h = opts.height ?? 900;
  const texture = opts.texture ?? 35;
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  const ctx = c.getContext('2d')!;
  let seed = 7;
  const rnd = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 2 ** 32;
  };
  for (let y = 0; y < h; y += 8) {
    for (let x = 0; x < w; x += 8) {
      const d = (rnd() - 0.5) * 2 * texture;
      const [r, g, b] = base.map((v) => Math.max(0, Math.min(255, v + d)));
      ctx.fillStyle = `rgb(${r | 0},${g | 0},${b | 0})`;
      ctx.fillRect(x, y, 8, 8);
    }
  }
  const blob: Blob = await new Promise((res) => c.toBlob((b) => res(b!), 'image/jpeg', 0.9));
  return new File([blob], name, { type: 'image/jpeg' });
}

function referenceTensor(): Float32Array {
  const n = 224 * 224;
  const t = new Float32Array(3 * n);
  const shift = [0.5, -0.2, 0.9];
  for (let c = 0; c < 3; c++) for (let i = 0; i < n; i++) t[c * n + i] = Math.sin(0.0001 * (i + 1) * (c + 1)) + shift[c];
  return t;
}

(window as unknown as { __jani: unknown }).__jani = {
  engine,
  makeLeafFile,
  referenceProbs: () => inferProbsForTest(referenceTensor()),
  ready: true,
};

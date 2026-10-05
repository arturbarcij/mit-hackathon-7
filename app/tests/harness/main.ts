import { createElement, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import * as engine from '../../src/engine';
import { useCheck, useConsent, useEngine, useOnline } from '../../src/hooks/useEngine';
import { inferProbsForTest } from '../../src/engine/model';
import { cropForModel } from '../../src/engine/preprocess';

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

/** RGB bytes of the 224 x 224 crop the model would see, for comparison with a Python reference. */
async function cropBytes(file: File, resizeTo?: number): Promise<number[]> {
  const bmp = await engine.bitmapFromFile(file);
  const data = cropForModel(bmp, { size: 224, resize: 'shorter_side_then_center_crop', resize_to: resizeTo, mean: [0, 0, 0], std: [1, 1, 1], layout: 'NCHW', range: '0-1' }).data;
  const out: number[] = [];
  for (let i = 0; i < data.length; i += 4) out.push(data[i], data[i + 1], data[i + 2]);
  return out;
}

/** Mounts a component that uses the real hooks and publishes their latest values on window.__probe. */
function mountProbe() {
  function Probe() {
    const eng = useEngine();
    const check = useCheck({ lang: 'sw', memberId: 'OCC0412', plotId: '2' });
    const consent = useConsent();
    const online = useOnline();
    useEffect(() => {
      (window as unknown as { __probe: unknown }).__probe = { eng, check, consent, online };
    });
    return null;
  }
  const host = document.createElement('div');
  document.body.appendChild(host);
  createRoot(host).render(createElement(Probe));
}

/** Applies a synthetic degradation to a real photo and returns the quality numbers the engine sees. */
async function qualityOf(file: File, opts: { blurPx?: number; brightness?: number; maxSide?: number } = {}) {
  const bmp = await engine.bitmapFromFile(file, opts.maxSide ?? 1600);
  let target: ImageBitmap = bmp;
  if (opts.blurPx || opts.brightness) {
    const c = document.createElement('canvas');
    c.width = bmp.width;
    c.height = bmp.height;
    const ctx = c.getContext('2d')!;
    ctx.filter = `${opts.blurPx ? `blur(${opts.blurPx}px)` : ''} ${opts.brightness ? `brightness(${opts.brightness})` : ''}`.trim();
    ctx.drawImage(bmp, 0, 0);
    target = await createImageBitmap(c);
  }
  return { width: bmp.width, height: bmp.height, ...engine.checkQuality(target) };
}

(window as unknown as { __jani: unknown }).__jani = {
  qualityOf,
  mountProbe,
  cropBytes,
  engine,
  makeLeafFile,
  referenceProbs: () => inferProbsForTest(referenceTensor()),
  ready: true,
};

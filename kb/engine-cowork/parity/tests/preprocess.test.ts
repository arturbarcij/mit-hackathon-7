/**
 * Preprocessing parity test. Run with: npx tsx tests/preprocess.test.ts <fixtures_dir> [out.json]
 *
 * For every fixture: decode PNG (pngjs) and JPEG (jpeg-js), run preprocess(),
 * compare against the tensor and 8 bit crop produced by torchvision in Python.
 * Exits non zero if the PNG path is not within 1/255 before normalisation.
 */
import * as fs from 'node:fs';
import * as path from 'node:path';
import { PNG } from 'pngjs';
import * as jpeg from 'jpeg-js';
import { preprocess, DEFAULT_SPEC } from '../src/preprocess';

const fixDir = process.argv[2] ?? path.join(__dirname, '..', '_work', 'fixtures');
const outPath = process.argv[3];

interface Fixture { name: string; kind: string; width: number; height: number; png: string; jpg: string }
const meta = JSON.parse(fs.readFileSync(path.join(fixDir, 'fixtures.json'), 'utf8')) as { fixtures: Fixture[]; pillow: string; torchvision: string };

function readF32(p: string): Float32Array {
  const b = fs.readFileSync(p);
  return new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength));
}

function compare(got: Float32Array, exp: Float32Array, gotRgb: Uint8Array, expRgb: Uint8Array) {
  if (got.length !== exp.length) throw new Error(`length ${got.length} vs ${exp.length}`);
  let maxAbs = 0;
  let sumAbs = 0;
  let exact = 0;
  for (let i = 0; i < got.length; i++) {
    const d = Math.abs(got[i] - exp[i]);
    if (d === 0) exact++;
    if (d > maxAbs) maxAbs = d;
    sumAbs += d;
  }
  let maxLvl = 0;
  let sumLvl = 0;
  let lvlExact = 0;
  const hist = new Map<number, number>();
  for (let i = 0; i < gotRgb.length; i++) {
    const d = Math.abs(gotRgb[i] - expRgb[i]);
    if (d === 0) lvlExact++;
    if (d > maxLvl) maxLvl = d;
    sumLvl += d;
    hist.set(d, (hist.get(d) ?? 0) + 1);
  }
  return {
    tensor_max_abs: maxAbs,
    tensor_mean_abs: sumAbs / got.length,
    tensor_exact_frac: exact / got.length,
    levels_max_abs: maxLvl,
    levels_mean_abs: sumLvl / gotRgb.length,
    levels_exact_frac: lvlExact / gotRgb.length,
    levels_hist: Object.fromEntries([...hist.entries()].sort((a, b) => a[0] - b[0])),
  };
}

const results: Record<string, unknown>[] = [];
let fail = false;
for (const f of meta.fixtures) {
  // PNG path (lossless): isolates the resize + crop + normalise maths.
  const pngBuf = fs.readFileSync(path.join(fixDir, f.png));
  const png = PNG.sync.read(pngBuf); // RGBA
  const t0 = performance.now();
  const outPng = preprocess({ data: png.data, width: png.width, height: png.height }, DEFAULT_SPEC);
  const msPng = performance.now() - t0;
  const cmpPng = compare(outPng.tensor, readF32(path.join(fixDir, f.png + '.bin')), outPng.rgb, new Uint8Array(fs.readFileSync(path.join(fixDir, f.png + '.rgb'))));

  // JPEG path: jpeg-js decoder vs PIL's libjpeg. Differences here are decoder differences, not resize.
  const jpgBuf = fs.readFileSync(path.join(fixDir, f.jpg));
  const jpg = jpeg.decode(jpgBuf, { useTArray: true, formatAsRGBA: true, maxMemoryUsageInMB: 1024, maxResolutionInMP: 100 });
  const t1 = performance.now();
  const outJpg = preprocess({ data: jpg.data, width: jpg.width, height: jpg.height }, DEFAULT_SPEC);
  const msJpg = performance.now() - t1;
  const cmpJpg = compare(outJpg.tensor, readF32(path.join(fixDir, f.jpg + '.bin')), outJpg.rgb, new Uint8Array(fs.readFileSync(path.join(fixDir, f.jpg + '.rgb'))));

  // Also: how much of the JPEG difference is the decoder itself? Decode the JPEG in Node,
  // and compare the JPEG-decoded preprocess output with the PNG-decoded one (same source pixels before JPEG).
  const ok = cmpPng.levels_max_abs <= 1;
  if (!ok) fail = true;
  results.push({
    name: f.name, kind: f.kind, width: f.width, height: f.height,
    resized: outPng.resized, crop: outPng.crop,
    png: { ...cmpPng, preprocess_ms: +msPng.toFixed(1) },
    jpg: { ...cmpJpg, preprocess_ms: +msJpg.toFixed(1) },
    ok,
  });
  console.log(
    `${ok ? 'PASS' : 'FAIL'} ${f.name.padEnd(28)} png: max=${cmpPng.levels_max_abs} lvl, exact=${(cmpPng.levels_exact_frac * 100).toFixed(2)}%  ` +
    `jpg: max=${cmpJpg.levels_max_abs} lvl, mean=${cmpJpg.levels_mean_abs.toFixed(4)} lvl, exact=${(cmpJpg.levels_exact_frac * 100).toFixed(2)}%  (${msPng.toFixed(0)} ms)`,
  );
}

const summary = {
  pillow: meta.pillow, torchvision: meta.torchvision, node: process.version,
  n: results.length,
  png_max_levels: Math.max(...results.map((r) => (r.png as { levels_max_abs: number }).levels_max_abs)),
  png_max_tensor_abs: Math.max(...results.map((r) => (r.png as { tensor_max_abs: number }).tensor_max_abs)),
  png_all_bit_exact: results.every((r) => (r.png as { tensor_exact_frac: number }).tensor_exact_frac === 1),
  jpg_max_levels: Math.max(...results.map((r) => (r.jpg as { levels_max_abs: number }).levels_max_abs)),
  jpg_max_tensor_abs: Math.max(...results.map((r) => (r.jpg as { tensor_max_abs: number }).tensor_max_abs)),
  jpg_mean_levels: results.reduce((a, r) => a + (r.jpg as { levels_mean_abs: number }).levels_mean_abs, 0) / results.length,
  per_image: results,
};
console.log(JSON.stringify({ ...summary, per_image: undefined }, null, 2));
if (outPath) fs.writeFileSync(outPath, JSON.stringify(summary, null, 2));
process.exit(fail ? 1 : 0);

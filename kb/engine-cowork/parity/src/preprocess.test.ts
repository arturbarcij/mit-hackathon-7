/**
 * Parity test for preprocess.ts against the torchvision oracle (py/oracle.py).
 * Run: node src/preprocess.test.ts [workDir]
 * (Node >= 22.18 strips types by default; older 22.x needs --experimental-strip-types.)
 * Exit code 1 if any exact-path output differs from the oracle.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { preprocess, resizeAndCrop, resizeWindow } from "./preprocess.ts";

const here = dirname(fileURLToPath(import.meta.url));
const work = process.argv[2] ?? join(here, "..", "work");
const logName = process.argv[2] ? `preprocess_test_${work.replace(/\/+$/, "").split("/").pop()}.json` : "preprocess_test.json";
const meta = JSON.parse(readFileSync(join(work, "index.json"), "utf8"));

function maxAbsU8(a: Uint8Array, b: Uint8Array): { max: number; count: number } {
  if (a.length !== b.length) throw new Error(`length ${a.length} vs ${b.length}`);
  let max = 0;
  let count = 0;
  for (let i = 0; i < a.length; i++) {
    const d = Math.abs(a[i] - b[i]);
    if (d > 0) count++;
    if (d > max) max = d;
  }
  return { max, count };
}

function maxAbsF32(a: Float32Array, b: Float32Array): number {
  if (a.length !== b.length) throw new Error(`length ${a.length} vs ${b.length}`);
  let max = 0;
  for (let i = 0; i < a.length; i++) {
    const d = Math.abs(a[i] - b[i]);
    if (d > max) max = d;
  }
  return max;
}

const u8 = (p: string) => new Uint8Array(readFileSync(p));
const f32 = (p: string) => {
  const b = readFileSync(p);
  return new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength));
};

const rows: Record<string, unknown>[] = [];
let worstResize = 0;
let worstCrop = 0;
let worstTensor = 0;
let fail = 0;
for (const it of meta.items) {
  const rgba = u8(join(work, `${it.name}.rgba`));
  const resizedRef = u8(join(work, `${it.name}.resized`));
  const cropRef = u8(join(work, `${it.name}.crop`));
  const tensorRef = f32(join(work, `${it.name}.tensor`));

  // 1. full Resize output (whole window), compared with PIL
  let full: Uint8Array;
  if (it.rw === it.w && it.rh === it.h) {
    full = new Uint8Array(it.w * it.h * 3);
    for (let i = 0, j = 0; i < it.w * it.h; i++, j += 4) {
      full[i * 3] = rgba[j];
      full[i * 3 + 1] = rgba[j + 1];
      full[i * 3 + 2] = rgba[j + 2];
    }
  } else {
    full = resizeWindow(rgba, it.w, it.h, 4, it.rw, it.rh, 0, 0, it.rw, it.rh);
  }
  const dr = maxAbsU8(full, resizedRef);
  // 2. resize + crop (windowed computation used by preprocess)
  const dc = maxAbsU8(resizeAndCrop(rgba, it.w, it.h), cropRef);
  // 3. full tensor
  const t = preprocess(rgba, it.w, it.h);
  const dt = maxAbsF32(t, tensorRef);
  worstResize = Math.max(worstResize, dr.max);
  worstCrop = Math.max(worstCrop, dc.max);
  worstTensor = Math.max(worstTensor, dt);
  const ok = dr.max === 0 && dc.max === 0 && dt === 0;
  if (!ok) fail++;
  const row: Record<string, unknown> = {
    name: it.name,
    size: `${it.w}x${it.h}`,
    resized: `${it.rw}x${it.rh}`,
    resizeMaxDiff: dr.max,
    resizeDiffCount: dr.count,
    cropMaxDiff: dc.max,
    tensorMaxDiff: dt,
    ok,
  };
  // 4. fast path: drift against the exact path, and equality with Pillow reducing_gap=2.0
  if (it.rg2) {
    const fast = resizeAndCrop(rgba, it.w, it.h, { fastPath: true });
    const vsExact = maxAbsU8(fast, cropRef);
    const vsRg2 = maxAbsU8(fast, u8(join(work, `${it.name}.rg2`)));
    const tf = preprocess(rgba, it.w, it.h, { fastPath: true });
    row.fastVsExactU8Max = vsExact.max;
    row.fastVsExactU8Count = vsExact.count;
    row.fastVsExactTensorMax = maxAbsF32(tf, tensorRef);
    row.fastVsPillowReducingGap2U8Max = vsRg2.max;
  }
  rows.push(row);
}

// 5. speed on 4000x3000 (synthetic noise; content does not change the cost)
function bench(fast: boolean): { medianMs: number; minMs: number; runs: number } {
  const w = 4000;
  const h = 3000;
  const px = new Uint8ClampedArray(w * h * 4);
  let s = 12345;
  for (let i = 0; i < px.length; i++) {
    s = (s * 1103515245 + 12345) >>> 0;
    px[i] = s >>> 24;
  }
  preprocess(px, w, h, { fastPath: fast }); // warm-up (JIT)
  const times: number[] = [];
  for (let r = 0; r < 7; r++) {
    const t0 = performance.now();
    preprocess(px, w, h, { fastPath: fast });
    times.push(performance.now() - t0);
  }
  times.sort((a, b) => a - b);
  return { medianMs: +times[3].toFixed(1), minMs: +times[0].toFixed(1), runs: times.length };
}
const speed = { exact_4000x3000: bench(false), fast_4000x3000: bench(true) };

const summary = {
  oracle: meta.oracle,
  pillow: meta.pillow,
  node: process.version,
  items: rows.length,
  failures: fail,
  worstResizeU8Diff: worstResize,
  worstCropU8Diff: worstCrop,
  worstTensorAbsDiff: worstTensor,
  speed,
};
console.table(rows.map((r) => ({ ...r })));
console.log(JSON.stringify(summary, null, 2));
const logDir = join(here, "..", "logs");
mkdirSync(logDir, { recursive: true });
writeFileSync(join(logDir, logName), JSON.stringify({ summary, rows }, null, 1));
process.exit(fail ? 1 : 0);

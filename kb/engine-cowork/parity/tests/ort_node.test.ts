/**
 * Run the fp32 and int8 test models with onnxruntime-web (wasm backend, numThreads 1) in Node,
 * on the same tensors Python used, and compare logits with Python onnxruntime.
 *
 * Usage: npx tsx tests/ort_node.test.ts <fixtures_dir> <model_dir> <python_logits.json> [out.json]
 */
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as ort from 'onnxruntime-web';

const [fixDir, modelDir, pyPath, outPath] = process.argv.slice(2);
ort.env.wasm.numThreads = 1;
ort.env.wasm.simd = true;

interface PyRow { name: string; tensor: string; pytorch: number[]; ort_fp32: number[]; ort_int8: number[] }
const py = JSON.parse(fs.readFileSync(pyPath, 'utf8')) as { per_image: PyRow[] };

function readF32(p: string): Float32Array {
  const b = fs.readFileSync(p);
  return new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength));
}
function argmax(a: ArrayLike<number>): number {
  let m = 0;
  for (let i = 1; i < a.length; i++) if (a[i] > a[m]) m = i;
  return m;
}
function maxAbs(a: ArrayLike<number>, b: ArrayLike<number>): number {
  let m = 0;
  for (let i = 0; i < a.length; i++) m = Math.max(m, Math.abs(a[i] - b[i]));
  return m;
}
function median(xs: number[]): number {
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)];
}

async function run(tag: 'fp32' | 'int8') {
  const file = path.join(modelDir, `test_${tag}.onnx`);
  const sess = await ort.InferenceSession.create(fs.readFileSync(file), { executionProviders: ['wasm'], graphOptimizationLevel: 'all' });
  const rows: Record<string, unknown>[] = [];
  const lat: number[] = [];
  for (const r of py.per_image) {
    const x = readF32(path.join(fixDir, r.tensor));
    const t0 = performance.now();
    const out = await sess.run({ input: new ort.Tensor('float32', x, [1, 3, 224, 224]) });
    lat.push(performance.now() - t0);
    const logits = Array.from(out.logits.data as Float32Array);
    const ref = tag === 'fp32' ? r.ort_fp32 : r.ort_int8;
    rows.push({
      name: r.name, logits,
      vs_python_ort_max_abs: maxAbs(logits, ref),
      vs_pytorch_max_abs: maxAbs(logits, r.pytorch),
      top1: argmax(logits), top1_python_ort: argmax(ref), top1_pytorch: argmax(r.pytorch),
    });
  }
  const n = rows.length;
  return {
    model_bytes: fs.statSync(file).size,
    vs_python_ort_max_abs: Math.max(...rows.map((r) => r.vs_python_ort_max_abs as number)),
    vs_pytorch_max_abs: Math.max(...rows.map((r) => r.vs_pytorch_max_abs as number)),
    top1_agree_python_ort: rows.filter((r) => r.top1 === r.top1_python_ort).length / n,
    top1_agree_pytorch: rows.filter((r) => r.top1 === r.top1_pytorch).length / n,
    latency_ms_median: +median(lat.slice(1)).toFixed(2),
    latency_ms_first: +lat[0].toFixed(2),
    per_image: rows,
  };
}

(async () => {
  const fp32 = await run('fp32');
  const int8 = await run('int8');
  const res = {
    onnxruntime_web: (ort.env as unknown as { versions?: { web?: string } }).versions?.web ?? JSON.parse(fs.readFileSync(path.join(path.dirname(require.resolve('onnxruntime-web/package.json')), 'package.json'), 'utf8')).version,
    node: process.version, numThreads: ort.env.wasm.numThreads, fp32, int8,
  };
  console.log(JSON.stringify({ ...res, fp32: { ...fp32, per_image: undefined }, int8: { ...int8, per_image: undefined } }, null, 2));
  if (outPath) fs.writeFileSync(outPath, JSON.stringify(res, null, 2));
})().catch((e) => { console.error(e); process.exit(1); });

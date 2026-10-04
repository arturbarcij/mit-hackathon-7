// onnxruntime-web (WASM, numThreads 1) in Node on preprocess.ts tensors,
// compared with Python onnxruntime on torchvision tensors.
// Usage: node js/run_ortweb.mjs <model.onnx> <workdir> <py_ref.json> <label> [pyKey]
import * as ort from "onnxruntime-web";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { preprocess } from "../src/preprocess.ts";

const here = dirname(fileURLToPath(import.meta.url));
const [modelPath, work, refPath, label, pyKey] = process.argv.slice(2);
const T = 1.5;
ort.env.wasm.numThreads = 1;
ort.env.wasm.simd = true;

const ref = JSON.parse(readFileSync(refPath, "utf8"));
const pyLogits = pyKey ? ref[pyKey] : ref.logits;
const meta = JSON.parse(readFileSync(join(work, "index.json"), "utf8"));

const softmax = (l, t) => {
  const z = l.map((v) => v / t);
  const m = Math.max(...z);
  const e = z.map((v) => Math.exp(v - m));
  const s = e.reduce((a, b) => a + b, 0);
  return e.map((v) => v / s);
};
const argmax = (a) => a.indexOf(Math.max(...a));

const t0 = performance.now();
const session = await ort.InferenceSession.create(readFileSync(modelPath), { executionProviders: ["wasm"], graphOptimizationLevel: "all" });
const createMs = performance.now() - t0;

const rows = [];
let maxLogit = 0, maxProb = 0, agree = 0;
const times = [];
for (const it of meta.items) {
  const rgba = new Uint8Array(readFileSync(join(work, `${it.name}.rgba`)));
  const x = preprocess(rgba, it.w, it.h);
  const s = performance.now();
  const out = await session.run({ input: new ort.Tensor("float32", x, [1, 3, 224, 224]) });
  times.push(performance.now() - s);
  const web = Array.from(out.logits.data);
  const py = pyLogits[it.name];
  const dl = Math.max(...web.map((v, i) => Math.abs(v - py[i])));
  const pw = softmax(web, T), pp = softmax(py, T);
  const dp = Math.max(...pw.map((v, i) => Math.abs(v - pp[i])));
  const same = argmax(web) === argmax(py);
  // margin between top-2 python logits: a top-1 flip below this margin is a near tie, not a bug
  const sorted = [...py].sort((a, b) => b - a);
  rows.push({ name: it.name, maxLogitDiff: +dl.toExponential(3), maxProbDiffT15: +dp.toExponential(3), top1Match: same, pyTop2Margin: +(sorted[0] - sorted[1]).toExponential(3) });
  maxLogit = Math.max(maxLogit, dl); maxProb = Math.max(maxProb, dp); agree += same ? 1 : 0;
}
const warm = times.slice(1).sort((a, b) => a - b);
const summary = {
  label, model: modelPath, ortWeb: ort.env.versions?.web ?? "?", node: process.version, numThreads: 1,
  pyOnnxruntime: ref.onnxruntime ?? "see fixture_model.json", items: rows.length,
  top1Agree: `${agree}/${rows.length}`, maxLogitDiff: maxLogit, maxProbDiffT15: maxProb,
  sessionCreateMs: +createMs.toFixed(1), firstRunMs: +times[0].toFixed(1), medianRunMs: +warm[Math.floor(warm.length / 2)].toFixed(1),
  inputs: session.inputNames, outputs: session.outputNames,
};
console.log(JSON.stringify(summary, null, 1));
mkdirSync(join(here, "..", "logs"), { recursive: true });
writeFileSync(join(here, "..", "logs", `ortweb_${label}.json`), JSON.stringify({ summary, rows }, null, 1));

#!/usr/bin/env node
// check_parity.mjs: does the browser path (preprocess.ts + onnxruntime-web WASM)
// reproduce app/ml/parity_samples/expected.json?
//
// Usage (from app/):
//   node tools/check_parity.mjs [--model public/model] [--samples ml/parity_samples]
//        [--preprocess src/engine/preprocess.ts] [--tol 0.02] [--json out.json]
// Needs Node >= 22.18 (imports the .ts file with built-in type stripping),
// devDependencies onnxruntime-web and sharp (sharp decodes JPEG with libjpeg-turbo,
// bit-identical to Pillow in our tests; jpeg-js is a fallback that is NOT identical).
// Per sample: top-1 must equal expected.label and max |prob - expected| <= tol.
// Exit 0 pass, 1 parity failure, 2 setup error.
import { readFileSync, readdirSync, writeFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => (a.startsWith("--") ? [...acc, [a.slice(2), all[i + 1]]] : acc), []),
);
const modelDir = resolve(args.model ?? "public/model");
const samplesDir = resolve(args.samples ?? "ml/parity_samples");
const preprocessPath = resolve(args.preprocess ?? "src/engine/preprocess.ts");
const tol = Number(args.tol ?? 0.02);

function die(msg) {
  console.error(`check_parity: ${msg}`);
  process.exit(2);
}
for (const p of [join(modelDir, "leaf.onnx"), join(modelDir, "model.json"), join(samplesDir, "expected.json"), preprocessPath]) {
  if (!existsSync(p)) die(`missing ${p}`);
}

const ort = await import("onnxruntime-web").catch(() => die("npm i -D onnxruntime-web"));
const { preprocess } = await import(pathToFileURL(preprocessPath).href);
if (typeof preprocess !== "function") die(`${preprocessPath} does not export preprocess(rgba, w, h)`);

// JPEG -> RGBA at native size, no EXIF rotation (Pillow does not rotate either).
let decode, decoderName;
try {
  const sharp = (await import("sharp")).default;
  decoderName = "sharp (libjpeg-turbo)";
  decode = async (buf) => {
    const { data, info } = await sharp(buf).removeAlpha().ensureAlpha().raw().toBuffer({ resolveWithObject: true });
    return { data: new Uint8ClampedArray(data.buffer, data.byteOffset, data.byteLength), width: info.width, height: info.height };
  };
} catch {
  try {
    const jpeg = (await import("jpeg-js")).default;
    decoderName = "jpeg-js (NOT bit-identical to Pillow; expect small extra drift)";
    decode = async (buf) => {
      const r = jpeg.decode(buf, { useTArray: true, formatAsRGBA: true });
      return { data: new Uint8ClampedArray(r.data.buffer), width: r.width, height: r.height };
    };
  } catch {
    die("npm i -D sharp (or jpeg-js as a fallback)");
  }
}

const modelBytes = readFileSync(join(modelDir, "leaf.onnx"));
const modelJson = JSON.parse(readFileSync(join(modelDir, "model.json"), "utf8"));
const expected = JSON.parse(readFileSync(join(samplesDir, "expected.json"), "utf8"));
const labels = modelJson.labels;
const T = expected.temperature ?? modelJson.temperature ?? 1;
const notes = [];
const sha = createHash("sha256").update(modelBytes).digest("hex");
if (modelJson.sha256 && modelJson.sha256 !== sha) notes.push(`model.json sha256 ${modelJson.sha256.slice(0, 12)} != leaf.onnx ${sha.slice(0, 12)}`);
if (modelJson.bytes && modelJson.bytes !== modelBytes.length) notes.push(`model.json bytes ${modelJson.bytes} != ${modelBytes.length}`);
if (modelJson.temperature !== undefined && expected.temperature !== undefined && modelJson.temperature !== expected.temperature)
  notes.push(`temperature differs: model.json ${modelJson.temperature} vs expected.json ${expected.temperature}`);
const pp = expected.preprocess ?? {};
if (pp.size && pp.size !== 224) notes.push(`expected.preprocess.size ${pp.size} != 224`);
if (pp.resize && pp.resize !== "shorter_side_then_center_crop") notes.push(`unexpected resize ${pp.resize}`);

ort.env.wasm.numThreads = 1;
const session = await ort.InferenceSession.create(modelBytes, { executionProviders: ["wasm"] });
const inName = session.inputNames[0];
const outName = session.outputNames.includes("logits") ? "logits" : session.outputNames[0];

const softmax = (l) => {
  const z = Array.from(l, (v) => v / T);
  const m = Math.max(...z);
  const e = z.map((v) => Math.exp(v - m));
  const s = e.reduce((a, b) => a + b, 0);
  return e.map((v) => v / s);
};

const rows = [];
let failures = 0;
for (const s of expected.samples) {
  const img = await decode(readFileSync(join(samplesDir, s.file)));
  const x = preprocess(img.data, img.width, img.height);
  const out = await session.run({ [inName]: new ort.Tensor("float32", x, [1, 3, 224, 224]) });
  const probs = softmax(out[outName].data);
  const top = labels[probs.indexOf(Math.max(...probs))];
  const maxDiff = Math.max(...labels.map((k, i) => Math.abs(probs[i] - (s.probs[k] ?? NaN))));
  const ok = top === s.label && maxDiff <= tol;
  if (!ok) failures++;
  rows.push({ file: s.file, size: `${img.width}x${img.height}`, expected: s.label, got: top, maxProbDiff: +maxDiff.toFixed(5), ok });
}
const worst = Math.max(...rows.map((r) => r.maxProbDiff));
const summary = {
  pass: failures === 0, samples: rows.length, failures, tol, worstMaxProbDiff: worst, temperature: T,
  decoder: decoderName, ortWeb: ort.env.versions?.web, node: process.version, preprocess: preprocessPath, notes,
};
console.table(rows);
console.log(JSON.stringify(summary, null, 1));
if (args.json) writeFileSync(args.json, JSON.stringify({ summary, rows }, null, 1));
process.exit(failures ? 1 : 0);

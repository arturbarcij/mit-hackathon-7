// Browser parity probe: createImageBitmap -> OffscreenCanvas.getImageData -> preprocess.ts -> onnxruntime-web/wasm
import * as ort from "onnxruntime-web/wasm";
import { preprocess } from "../src/preprocess.ts";
ort.env.wasm.numThreads = 1;
ort.env.wasm.wasmPaths = "/ort/";
async function decode(url, orientation) {
  const blob = await (await fetch(url)).blob();
  const bmp = await createImageBitmap(blob, orientation ? { imageOrientation: orientation } : undefined);
  const c = new OffscreenCanvas(bmp.width, bmp.height);
  const g = c.getContext("2d", { willReadFrequently: true });
  g.drawImage(bmp, 0, 0);
  return g.getImageData(0, 0, bmp.width, bmp.height);
}
window.runParity = async (modelUrl, files, orientation) => {
  const t0 = performance.now();
  const s = await ort.InferenceSession.create(modelUrl, { executionProviders: ["wasm"] });
  const createMs = performance.now() - t0;
  const out = [];
  for (const f of files) {
    const a = performance.now();
    const im = await decode(`/img/${f}`, orientation);
    const b = performance.now();
    const x = preprocess(im.data, im.width, im.height);
    const c = performance.now();
    const r = await s.run({ input: new ort.Tensor("float32", x, [1, 3, 224, 224]) });
    const d = performance.now();
    out.push({ file: f, w: im.width, h: im.height, rgbaHead: Array.from(im.data.slice(0, 8)), logits: Array.from(r.logits.data),
      decodeMs: b - a, preprocessMs: c - b, runMs: d - c });
  }
  return { createMs, out, ua: navigator.userAgent };
};
window.dumpRgba = async (f, orientation) => { const im = await decode(`/img/${f}`, orientation); return { w: im.width, h: im.height, data: Array.from(im.data) }; };

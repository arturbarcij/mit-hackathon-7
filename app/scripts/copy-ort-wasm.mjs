#!/usr/bin/env node
// Copies the onnxruntime-web WASM runtime the engine needs into public/ort/.
// The engine imports 'onnxruntime-web/wasm' (plain WASM EP, no WebGPU/JSEP) with
// env.wasm.wasmPaths = '/ort/' and numThreads = 1, so only these two files are fetched.
// Run from app/: node scripts/copy-ort-wasm.mjs
import { copyFileSync, mkdirSync, statSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';

const FILES = ['ort-wasm-simd-threaded.wasm', 'ort-wasm-simd-threaded.mjs'];
const require = createRequire(import.meta.url);
let dist;
try {
  dist = join(dirname(require.resolve('onnxruntime-web/package.json')), 'dist');
} catch {
  dist = resolve('node_modules/onnxruntime-web/dist');
}
const out = resolve('public/ort');
mkdirSync(out, { recursive: true });
let total = 0;
for (const f of FILES) {
  const src = join(dist, f);
  if (!existsSync(src)) {
    console.error(`copy-ort-wasm: missing ${src} (npm install onnxruntime-web first)`);
    process.exit(1);
  }
  copyFileSync(src, join(out, f));
  const n = statSync(src).size;
  total += n;
  console.log(`${f}  ${(n / 1e6).toFixed(2)} MB`);
}
console.log(`total ${(total / 1e6).toFixed(2)} MB -> ${out}`);

// Copies the onnxruntime-web runtime into public/ort so it is served from our own origin and precached.
// The WASM binary is stored gzipped (11.2 MB becomes 2.9 MB), which keeps the offline precache small on every
// host. src/engine/model.ts inflates it in the browser. Run `npm run copy:ort` after changing the onnxruntime-web
// version, then commit the result.
import { copyFileSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync, constants } from 'node:zlib';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const from = join(root, 'node_modules', 'onnxruntime-web', 'dist');
const to = join(root, 'public', 'ort');
mkdirSync(to, { recursive: true });

copyFileSync(join(from, 'ort-wasm-simd-threaded.mjs'), join(to, 'ort-wasm-simd-threaded.mjs'));
console.log('copied ort-wasm-simd-threaded.mjs');

const wasm = readFileSync(join(from, 'ort-wasm-simd-threaded.wasm'));
const gz = gzipSync(wasm, { level: constants.Z_BEST_COMPRESSION });
writeFileSync(join(to, 'ort-wasm-simd-threaded.wasm.gz'), gz);
rmSync(join(to, 'ort-wasm-simd-threaded.wasm'), { force: true });
console.log(`wrote ort-wasm-simd-threaded.wasm.gz (${wasm.length} -> ${gz.length} bytes)`);

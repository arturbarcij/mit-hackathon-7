// Copies the onnxruntime-web WASM runtime into public/ort so it is served from our own origin and precached.
// Run `npm run copy:ort` after changing the onnxruntime-web version, then commit the result.
import { copyFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const from = join(root, 'node_modules', 'onnxruntime-web', 'dist');
const to = join(root, 'public', 'ort');
mkdirSync(to, { recursive: true });
for (const f of ['ort-wasm-simd-threaded.mjs', 'ort-wasm-simd-threaded.wasm']) {
  copyFileSync(join(from, f), join(to, f));
  console.log('copied', f);
}

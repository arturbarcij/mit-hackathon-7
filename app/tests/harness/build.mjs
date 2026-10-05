// Builds the engine harness into node_modules/.jani-harness/dist with the real PWA settings.
// If public/model has no model yet, the tiny fixture model is staged instead (it is NOT a coffee model).
import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { build } from 'vite';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const work = join(root, 'node_modules', '.jani-harness');
const stage = join(work, 'public');
rmSync(work, { recursive: true, force: true });
mkdirSync(stage, { recursive: true });
cpSync(join(root, 'public'), stage, { recursive: true });
const realModel = existsSync(join(root, 'public', 'model', 'leaf.onnx')) && existsSync(join(root, 'public', 'model', 'model.json'));
if (!realModel) cpSync(join(root, 'tests', 'fixtures', 'model'), join(stage, 'model'), { recursive: true });
console.log(realModel ? 'harness: using public/model' : 'harness: using fixture model');

await build({ configFile: join(root, 'vite.harness.config.ts'), logLevel: 'warn' });

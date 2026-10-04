// Runs tsc --noEmit on tests/types-check.ts with '@engine-under-test' pointed at the
// engine. A drifted signature or missing export fails this test with tsc's message.
import { spawnSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { ENGINE_PATH } from './engine-under-test';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');

describe('types (compile-time)', () => {
  it(`engine exports match the CONTRACTS signatures (tsc --noEmit, engine ${ENGINE_PATH})`, () => {
    const workDir = path.join(root, '_work', 'typecheck');
    mkdirSync(workDir, { recursive: true });
    const cfgPath = path.join(workDir, 'tsconfig.engine.json');
    const cfg = {
      extends: path.join(root, 'tsconfig.json'),
      compilerOptions: {
        noEmit: true,
        baseUrl: root,
        rootDir: '/',
        paths: { '@engine-under-test': [ENGINE_PATH] },
        types: ['node'],
      },
      include: [path.join(root, 'tests', 'types-check.ts'), path.join(root, 'reference', 'types.ts')],
      exclude: [],
    };
    writeFileSync(cfgPath, JSON.stringify(cfg, null, 2));
    const tsc = path.join(root, 'node_modules', 'typescript', 'bin', 'tsc');
    const r = spawnSync(process.execPath, [tsc, '--noEmit', '-p', cfgPath], { encoding: 'utf8', cwd: root });
    const out = (r.stdout ?? '') + (r.stderr ?? '');
    expect(r.status, `tsc failed:\n${out}`).toBe(0);
  });
});

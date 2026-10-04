// @vitest-environment node
// Guard: the engine runs on the phone. No cloud AI API may appear in engine or hook code.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const ROOT = fileURLToPath(new URL('../../', import.meta.url));
const DIRS = ['src/engine', 'src/hooks'];
const BANNED = ['openai', 'anthropic', 'generativelanguage', 'elevenlabs', 'api.mistral', 'cohere', 'huggingface.co'];

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

describe('no cloud AI APIs in the engine', () => {
  const files = DIRS.flatMap((d) => walk(join(ROOT, d)));

  it('finds the engine and hook sources', () => {
    expect(files.length).toBeGreaterThanOrEqual(10);
  });

  it('has no banned AI API string (case-insensitive)', () => {
    const hits: string[] = [];
    for (const f of files) {
      const text = readFileSync(f, 'utf8').toLowerCase();
      for (const word of BANNED) if (text.includes(word)) hits.push(`${relative(ROOT, f)}: ${word}`);
    }
    expect(hits).toEqual([]);
  });
});

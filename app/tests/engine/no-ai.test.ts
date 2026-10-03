import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const root = join(dirname(fileURLToPath(import.meta.url)), '../../src');
const banned = ['openai', 'anthropic', 'generativelanguage', 'elevenlabs'];

function filesIn(dir: string): string[] {
  const found: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) found.push(...filesIn(path));
    else if (/\.(ts|tsx|js|mjs)$/.test(entry.name)) found.push(path);
  }
  return found;
}

describe('client engine has no AI API hosts', () => {
  it('does not mention a runtime model API', () => {
    const files = [...filesIn(join(root, 'engine')), ...filesIn(join(root, 'hooks'))];
    expect(files.length).toBeGreaterThan(0);
    const hits: string[] = [];
    for (const file of files) {
      const text = readFileSync(file, 'utf8').toLowerCase();
      for (const word of banned) {
        if (text.includes(word)) hits.push(`${file} contains ${word}`);
      }
    }
    expect(hits).toEqual([]);
  });
});

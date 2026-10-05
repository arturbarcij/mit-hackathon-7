import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const FORBIDDEN = ['openai', 'anthropic', 'generativelanguage', 'elevenlabs', 'api.groq', 'huggingface.co/api', 'api-inference'];

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (/\.(ts|tsx|js|jsx|json|html|css)$/.test(name)) out.push(p);
  }
  return out;
}

describe('no runtime AI services in the client', () => {
  it('src and index.html never mention an AI API', () => {
    const files = [...walk(join(__dirname, '../../src')), join(__dirname, '../../index.html')];
    expect(files.length).toBeGreaterThan(5);
    const hits: string[] = [];
    for (const f of files) {
      const text = readFileSync(f, 'utf8').toLowerCase();
      for (const word of FORBIDDEN) if (text.includes(word)) hits.push(`${f}: ${word}`);
    }
    expect(hits).toEqual([]);
  });

  it('no VITE_ variable carries a secret-looking name', () => {
    const files = walk(join(__dirname, '../../src'));
    const bad: string[] = [];
    for (const f of files) {
      const text = readFileSync(f, 'utf8');
      for (const m of text.matchAll(/VITE_[A-Z0-9_]+/g)) {
        if (/SECRET|SERVICE_ROLE|API_KEY|PRIVATE|PASSWORD/.test(m[0])) bad.push(`${f}: ${m[0]}`);
      }
    }
    expect(bad).toEqual([]);
  });

  it('no em dashes in engine source', () => {
    const bad = walk(join(__dirname, '../../src/engine')).filter((f) => readFileSync(f, 'utf8').includes('\u2014'));
    expect(bad).toEqual([]);
  });
});

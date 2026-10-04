// Static guardrails on the engine folder (mirrors app/qa/checks/client_clean.py) and on the bank.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { answersById, ENGINE_DIR, rules } from './helpers';

const FORBIDDEN_HOSTS = ['api.openai.com', 'api.anthropic.com', 'generativelanguage.googleapis.com', 'api.elevenlabs.io',
  'api.brightdata.com', 'mcp.brightdata.com', 'api-inference.huggingface.co', 'openrouter.ai', 'api.mistral.ai', 'api.cohere.'];
const FORBIDDEN_PKGS = ["from 'openai'", 'from "openai"', '@anthropic-ai/sdk', '@google/generative-ai', 'elevenlabs', '@google/genai'];
const SECRET_RE = /(sk-[A-Za-z0-9]{20,}|sk_[a-z]+_[A-Za-z0-9]{16,}|AIza[0-9A-Za-z\-_]{30,}|xi-api-key\s*[:=]\s*['"][A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|token=[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/;
const VITE_SECRET_RE = /VITE_[A-Z_]*(KEY|SECRET|TOKEN|PASSWORD)/;
const EXTS = new Set(['.ts', '.tsx', '.js', '.jsx', '.json', '.html', '.css']);

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((f) => {
    const p = path.join(dir, f);
    if (f === 'node_modules' || f.startsWith('.')) return [];
    return statSync(p).isDirectory() ? walk(p) : EXTS.has(path.extname(f)) ? [p] : [];
  });
}
const files = walk(ENGINE_DIR).map((p) => ({ rel: path.relative(ENGINE_DIR, p), txt: readFileSync(p, 'utf-8') }));
const code = (txt: string) => txt.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');

describe(`guardrails: engine source (${files.length} files)`, () => {
  it('has source files to scan', () => expect(files.length).toBeGreaterThan(0));

  it('references no AI API hosts or SDKs', () => {
    const hits = files.flatMap((f) => [...FORBIDDEN_HOSTS, ...FORBIDDEN_PKGS].filter((h) => f.txt.includes(h)).map((h) => `${f.rel}: ${h}`));
    expect(hits).toEqual([]);
  });

  it('contains no secrets or VITE_*KEY variables', () => {
    expect(files.filter((f) => SECRET_RE.test(f.txt) || VITE_SECRET_RE.test(f.txt)).map((f) => f.rel)).toEqual([]);
  });

  it('never opens a window or assigns location (nothing is sent without a user tap)', () => {
    const re = /window\.open\s*\(|(?:window\.|document\.|globalThis\.|\b)location(?:\.href)?\s*=(?!=)|location\.(?:assign|replace)\s*\(/;
    expect(files.filter((f) => re.test(code(f.txt))).map((f) => f.rel)).toEqual([]);
  });

  it('never sends SMS itself (no sms: navigation, no SMS gateway call)', () => {
    const re = /(window\.open|location(?:\.href)?\s*=|location\.assign)\s*\(?[^;\n]*sms:|navigator\.sendBeacon|twilio|africastalking/i;
    expect(files.filter((f) => re.test(code(f.txt))).map((f) => f.rel)).toEqual([]);
  });
});

describe('guardrails: answer bank and rules', () => {
  it('every answer id referenced in rules.json exists in answers.json with sw and en text', () => {
    const bad = rules.map((r: any) => r.then).filter((id: string) => !answersById.get(id)?.text?.sw || !answersById.get(id)?.text?.en);
    expect(bad).toEqual([]);
  });
  it('the last rule is the ask_officer catch-all', () => {
    expect(rules[rules.length - 1]).toMatchObject({ if: {}, then: 'ask_officer' });
  });
  it('rules use only the condition keys allowed by CONTRACTS', () => {
    const allowed = new Set(['dominant', 'affected_gte', 'affected_lte', 'uncertain_gte', 'distinct_problems_gte', 'window']);
    expect(rules.flatMap((r: any) => Object.keys(r.if ?? {})).filter((k: string) => !allowed.has(k))).toEqual([]);
  });
  it('not_a_leaf (the capture-time retake prompt) and ask_officer exist with sw and en text', () => {
    for (const id of ['not_a_leaf', 'ask_officer', 'too_many_unsure']) expect(answersById.get(id)?.text?.sw && answersById.get(id)?.text?.en, id).toBeTruthy();
  });
});

// Evaluates the quality gate on real phone photos (BRACOL, Brazil, CC BY 4.0) and the Uganda set.
// Usage: JANI_DATA=/path/to/data node tests/eval/quality.mjs
// Expects $JANI_DATA/bracol/**/images/*.jpg and $JANI_DATA/uganda/**/*.jpg (see kb/research/DATASETS.md).
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { openHarness } from './with-harness.mjs';

const root = process.env.JANI_DATA;
if (!root) throw new Error('Set JANI_DATA to the folder holding bracol/ and uganda/');

function walk(dir, out = []) {
  for (const n of readdirSync(dir)) {
    const p = join(dir, n);
    statSync(p).isDirectory() ? walk(p, out) : /\.jpe?g$/i.test(n) && statSync(p).size > 0 && out.push(p);
  }
  return out;
}
function sample(arr, n) {
  const step = Math.max(1, Math.floor(arr.length / n));
  return arr.filter((_, i) => i % step === 0).slice(0, n);
}
const pct = (a, q) => [...a].sort((x, y) => x - y)[Math.min(a.length - 1, Math.floor(q * a.length))];

const sets = {
  bracol: sample(walk(join(root, 'bracol')), 120),
  uganda: sample(walk(join(root, 'uganda')), 120),
};
const variants = [
  { name: 'original' },
  { name: 'blur 2px', blurPx: 2 }, { name: 'blur 4px', blurPx: 4 }, { name: 'blur 8px', blurPx: 8 },
  { name: 'blur 16px', blurPx: 16 }, { name: 'blur 32px', blurPx: 32 },
  { name: 'brightness 0.5', brightness: 0.5 }, { name: 'brightness 0.3', brightness: 0.3 }, { name: 'brightness 0.15', brightness: 0.15 },
];

const { page, close } = await openHarness();
const rows = [];
for (const [setName, files] of Object.entries(sets)) {
  for (const v of variants) {
    const res = [];
    for (const f of files) {
      const b64 = readFileSync(f).toString('base64');
      res.push(await page.evaluate(([n, b64, opts]) => {
        const bin = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
        return window.__jani.qualityOf(new File([bin], n, { type: 'image/jpeg' }), opts);
      }, [f, b64, v]));
    }
    const reasons = res.reduce((m, r) => ((m[r.reason ?? 'ok'] = (m[r.reason ?? 'ok'] ?? 0) + 1), m), {});
    rows.push({ set: setName, variant: v.name, n: res.length, accepted: reasons.ok ?? 0, reasons,
      blurP5: +pct(res.map((r) => r.blur), 0.05).toFixed(5), blurP50: +pct(res.map((r) => r.blur), 0.5).toFixed(5),
      brightP5: Math.round(pct(res.map((r) => r.brightness), 0.05)), brightP50: Math.round(pct(res.map((r) => r.brightness), 0.5)) });
  }
}
await close();
console.table(rows.map((r) => ({ ...r, reasons: JSON.stringify(r.reasons) })));

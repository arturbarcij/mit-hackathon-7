// Compares the browser's 224 px model crop with a PIL reference on real photos.
// Usage: JANI_DATA=/path/to/data node tests/eval/preprocess.mjs   (needs python3 with Pillow and numpy)
// The browser runs bitmapFromFile (decode, longer side limited to 1600 px) then the engine crop. The reference
// does the same limit, then PIL resize of the shorter side to 224 and a centre crop.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { openHarness } from './with-harness.mjs';

const root = process.env.JANI_DATA;
if (!root) throw new Error('Set JANI_DATA');
function walk(dir, out = []) {
  for (const n of readdirSync(dir)) {
    const p = join(dir, n);
    statSync(p).isDirectory() ? walk(p, out) : /\.jpe?g$/i.test(n) && statSync(p).size > 0 && out.push(p);
  }
  return out;
}
const pick = (a, n) => a.filter((_, i) => i % Math.floor(a.length / n) === 0).slice(0, n);
const files = [...pick(walk(join(root, 'bracol')), 12), ...pick(walk(join(root, 'uganda')), 12)];

const out = join(root, '_parity');
mkdirSync(out, { recursive: true });
const { page, close } = await openHarness(4181);
for (const [i, f] of files.entries()) {
  const b64 = readFileSync(f).toString('base64');
  const bytes = await page.evaluate(async ([n, b64]) => {
    const bin = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    return window.__jani.cropBytes(new File([bin], n, { type: 'image/jpeg' }));
  }, [f, b64]);
  writeFileSync(join(out, `${i}.json`), JSON.stringify({ src: f, bytes }));
}
await close();
const py = `
import json, glob, numpy as np
from PIL import Image
def ref(path, flt):
    im = Image.open(path).convert('RGB'); L = max(im.size)
    if L > 1600:
        s = 1600 / L; im = im.resize((round(im.width*s), round(im.height*s)), Image.BICUBIC)
    w, h = im.size; s = 224 / min(w, h)
    im = im.resize((max(224, round(w*s)), max(224, round(h*s))), flt)
    l, t = (im.width-224)//2, (im.height-224)//2
    return np.asarray(im.crop((l, t, l+224, t+224)), np.float32)
res = {'bracol': [], 'uganda': []}
for p in sorted(glob.glob('${out}/*.json')):
    d = json.load(open(p)); br = np.array(d['bytes'], np.float32).reshape(224, 224, 3)
    key = 'bracol' if 'bracol' in d['src'] else 'uganda'
    res[key].append([np.abs(br - ref(d['src'], f)).mean() for f in (Image.BILINEAR, Image.BICUBIC)])
for k, v in res.items():
    v = np.array(v); print(k, 'n=%d' % len(v), 'mean abs pixel diff (0-255) vs PIL bilinear: mean %.2f max %.2f | bicubic: mean %.2f max %.2f' % (v[:,0].mean(), v[:,0].max(), v[:,1].mean(), v[:,1].max()))
`;
console.log(execFileSync('python3', ['-c', py], { encoding: 'utf8' }));

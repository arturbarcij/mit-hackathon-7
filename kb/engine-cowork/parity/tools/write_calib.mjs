// Writes ~50 calibration tensors made by preprocess.ts (real images, plus
// deterministic sub-crops of the larger ones) to work/calib/NNN.f32.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { preprocess } from "../src/preprocess.ts";

const here = dirname(fileURLToPath(import.meta.url));
const work = join(here, "..", "work");
const out = join(work, "calib");
mkdirSync(out, { recursive: true });
const meta = JSON.parse(readFileSync(join(work, "index.json"), "utf8"));
const real = meta.items.filter((it) => it.source.startsWith("real:"));

let n = 0;
const save = (t) => writeFileSync(join(out, `${String(n++).padStart(3, "0")}.f32`), Buffer.from(t.buffer));
let seed = 42;
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) / 4294967296);

for (const it of real) {
  const rgba = new Uint8Array(readFileSync(join(work, `${it.name}.rgba`)));
  save(preprocess(rgba, it.w, it.h));
  if (Math.min(it.w, it.h) >= 448) {
    for (let k = 0; k < 3; k++) {
      const cw = Math.floor(it.w * (0.4 + 0.4 * rnd()));
      const ch = Math.floor(it.h * (0.4 + 0.4 * rnd()));
      const x0 = Math.floor((it.w - cw) * rnd());
      const y0 = Math.floor((it.h - ch) * rnd());
      const sub = new Uint8Array(cw * ch * 4);
      for (let y = 0; y < ch; y++) sub.set(rgba.subarray(((y0 + y) * it.w + x0) * 4, ((y0 + y) * it.w + x0 + cw) * 4), y * cw * 4);
      save(preprocess(sub, cw, ch));
    }
  }
}
// top up with flipped copies of the small images until 50
for (const it of real) {
  if (n >= 50) break;
  const rgba = new Uint8Array(readFileSync(join(work, `${it.name}.rgba`)));
  const f = new Uint8Array(rgba.length);
  for (let y = 0; y < it.h; y++) for (let x = 0; x < it.w; x++) {
    const s = (y * it.w + x) * 4, d = (y * it.w + (it.w - 1 - x)) * 4;
    f[d] = rgba[s]; f[d + 1] = rgba[s + 1]; f[d + 2] = rgba[s + 2]; f[d + 3] = 255;
  }
  save(preprocess(f, it.w, it.h));
}
console.log(`wrote ${n} calibration tensors to ${out}`);

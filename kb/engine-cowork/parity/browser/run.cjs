// Playwright Chromium probe. Usage: node browser/run.cjs
const { chromium } = require("/opt/npm-tools/node_modules/playwright");
const fs = require("fs"); const path = require("path");
const here = __dirname, root = path.join(here, "..");
(async () => {
  let browser;
  try { browser = await chromium.launch(); } catch (e) { browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" }); }
  const page = await browser.newPage();
  const reqs = [];
  page.on("request", (r) => reqs.push(r.url().replace("http://127.0.0.1:8765", "")));
  page.on("console", (m) => console.log("console:", m.text()));
  await page.goto("http://127.0.0.1:8765/index.html");
  await page.waitForFunction(() => typeof window.runParity === "function");
  const imgs = fs.readdirSync(path.join(here, "site/img")).filter((f) => /^\d\d_/.test(f)).sort();
  const ps = fs.readdirSync(path.join(here, "site/img")).filter((f) => /^\d\d\.jpg$/.test(f)).sort();
  const res = {};
  res.fixture_int8_images = await page.evaluate(([m, f]) => window.runParity(m, f), ["/model/fixture_int8.onnx", imgs]);
  res.leaf_images = await page.evaluate(([m, f]) => window.runParity(m, f), ["/model/leaf.onnx", imgs]);
  res.leaf_parity_samples = await page.evaluate(([m, f]) => window.runParity(m, f), ["/model/leaf.onnx", ps]);
  res.exif_default = await page.evaluate(() => window.dumpRgba("exif6.jpg"));
  res.exif_none = await page.evaluate(() => window.dumpRgba("exif6.jpg", "none"));
  res.exif_default = { w: res.exif_default.w, h: res.exif_default.h };
  const exifNone = res.exif_none; res.exif_none = { w: exifNone.w, h: exifNone.h };
  fs.writeFileSync(path.join(root, "work", "exif6_none.rgba"), Buffer.from(exifNone.data));
  // decoder parity: Chrome RGBA vs PIL RGBA for every real image
  res.decode = [];
  for (const f of [...imgs, ...ps]) {
    const d = await page.evaluate((f) => window.dumpRgba(f), f);
    const name = f.replace(".jpg", "");
    const pil = fs.readFileSync(path.join(root, /^\d\d\.jpg$/.test(f) ? "work_ps" : "work", name + ".rgba"));
    let mx = 0, cnt = 0;
    for (let i = 0; i < pil.length; i++) { if (i % 4 === 3) continue; const dd = Math.abs(pil[i] - d.data[i]); if (dd) cnt++; if (dd > mx) mx = dd; }
    res.decode.push({ file: f, w: d.w, h: d.h, maxU8DiffVsPIL: mx, diffCount: cnt });
  }
  res.requests = [...new Set(reqs)].filter((u) => !u.startsWith("/img/"));
  fs.writeFileSync(path.join(root, "logs", "browser_raw.json"), JSON.stringify(res));
  console.log(JSON.stringify({ requests: res.requests, decode: res.decode, exif_default: res.exif_default, exif_none: res.exif_none, ua: res.leaf_images.ua }, null, 0));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });

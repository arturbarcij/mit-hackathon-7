// Headless Chromium smoke test of the real engine (built bundle, /ort/ wasm, real leaf.onnx).
// From app/: npx vite build --config scripts/browser-smoke/vite.config.mjs
//            npx vite preview --config scripts/browser-smoke/vite.config.mjs --port 8790 --strictPort &
//            node scripts/browser-smoke/run.cjs
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/opt/npm-tools/node_modules/playwright');
const fs = require('fs'); const path = require('path');
(async () => {
  let browser;
  try { browser = await chromium.launch(); } catch (e) { browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' }); }
  const page = await browser.newPage();
  const reqs = []; page.on('request', (r) => reqs.push(r.url().replace('http://localhost:8790', '')));
  page.on('console', (m) => console.log('console:', m.type(), m.text().slice(0, 200)));
  await page.goto('http://localhost:8790/index.html');
  await page.waitForFunction(() => window.engineReady === true);
  const app = path.resolve(__dirname, '../..');
  const files = [
    ...fs.readdirSync(app + '/public/demo').filter((f) => f.endsWith('.jpg')).sort().map((f) => app + '/public/demo/' + f),
    ...['00', '05', '07'].map((n) => app + '/ml/parity_samples/' + n + '.jpg'),
    ...['syn_leaf_on_page.png', 'syn_skin_hand.png', 'syn_plain_page.png', 'syn_noise.png'].map((f) => app + '/tests/engine/fixtures/gate/' + f),
  ];
  const items = files.map((f) => ({ name: path.basename(f), b64: fs.readFileSync(f).toString('base64'), type: f.endsWith('.png') ? 'image/png' : 'image/jpeg' }));
  const res = await page.evaluate((items) => window.run(items), items);
  res.requests = [...new Set(reqs)];
  fs.writeFileSync(path.join(app, 'tests/engine/fixtures/demo_predictions_browser.json'), JSON.stringify(res, null, 1));
  console.log(JSON.stringify({ info: res.info, tLoad: res.tLoad, offscreen: res.offscreen, ua: res.ua, requests: res.requests }));
  for (const o of res.out) console.log(o.name.padEnd(22), String(o.gated).padEnd(8), String(o.reason).padEnd(12), o.sheet ? `${o.sheet.detail || 'ok'} p=${o.sheet.paper} e=${o.sheet.edge} l=${o.sheet.leaf}` : '-', '| raw', o.label, o.conf, 'blur', o.blur, 'br', o.bright, o.msGated + 'ms', o.msRaw + 'ms');
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });

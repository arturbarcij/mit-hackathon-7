// Offline end-to-end check for the static farmer PWA, at 360 x 740.
// 1. Serve the production build with `vite preview` (or use BASE_URL).
// 2. Load online, wait until the service worker has cached every file in the precache list.
// 3. Go offline, reload, run the sample plot end to end, reach the decision screen, choose
//    "Ask the officer" and check the referral SMS preview. Nothing is sent: Send is never tapped.
// Screens go to tests/e2e/screens/, results to tests/e2e/screens/result.json.
// MEASURE=1 adds a first-load timing at 1 Mbit/s (Chrome DevTools network throttling).
//
// Run: npm run build && node tests/e2e/offline-flow.mjs
// Playwright: uses the `playwright` package if installed, else the global one (PLAYWRIGHT_MODULE).
import { spawn } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..', '..');
const SCREENS = path.join(HERE, 'screens');
mkdirSync(SCREENS, { recursive: true });

function loadPlaywright() {
  const require = createRequire(import.meta.url);
  const candidates = [
    process.env.PLAYWRIGHT_MODULE,
    'playwright',
    '/home/claude/.npm-global/lib/node_modules/playwright',
    '/usr/local/lib/node_modules/playwright',
    '/usr/lib/node_modules/playwright',
  ].filter(Boolean);
  for (const c of candidates) {
    try {
      return require(c);
    } catch {
      // next
    }
  }
  throw new Error('playwright not found; set PLAYWRIGHT_MODULE to its folder');
}

const { chromium } = loadPlaywright();
const PORT = Number(process.env.PORT ?? 4173);
let BASE = process.env.BASE_URL;
let server = null;

async function startPreview() {
  // Refuse a port that already serves something: otherwise the test would run against another build.
  try {
    await fetch(`http://127.0.0.1:${PORT}/`);
    throw new Error(`port ${PORT} is already in use by another server; set PORT to a free port`);
  } catch (e) {
    if (String(e).includes('already in use')) throw e;
  }
  server = spawn('npx', ['vite', 'preview', '--port', String(PORT), '--strictPort', '--host', '127.0.0.1'], {
    cwd: APP,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const url = `http://127.0.0.1:${PORT}/`;
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch(url);
      if (r.ok) return url;
    } catch {
      // not up yet
    }
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error('vite preview did not start');
}

async function launch() {
  const opts = { headless: true };
  try {
    return await chromium.launch(opts);
  } catch (e) {
    const exe = process.env.CHROME_PATH ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
    console.warn(`[e2e] default chromium failed (${String(e).split('\n')[0]}), using ${exe}`);
    return chromium.launch({ ...opts, executablePath: exe });
  }
}

const log = [];
function note(msg) {
  const line = `[${new Date().toISOString().slice(11, 19)}] ${msg}`;
  log.push(line);
  console.log(line);
}

let step = 0;
async function shot(page, name) {
  step += 1;
  const file = `${String(step).padStart(2, '0')}-${name}.png`;
  await page.screenshot({ path: path.join(SCREENS, file), fullPage: true });
  note(`screenshot ${file}`);
}

async function waitOfflineReady(page, timeoutMs) {
  await page.waitForFunction(() => window.__janiOffline && window.__janiOffline.ready === true, null, { timeout: timeoutMs });
  // Double-check: every file in the precache list is in the cache.
  return page.evaluate(async () => {
    const m = await (await fetch('precache-manifest.json')).json();
    const keys = await caches.keys();
    const name = keys.find((k) => k === `jani-precache-${m.version}`);
    if (!name) return { ok: false, reason: 'cache missing', keys };
    const cache = await caches.open(name);
    const missing = [];
    for (const f of m.files) if (!(await cache.match(f.url))) missing.push(f.url);
    return { ok: missing.length === 0, version: m.version, files: m.files.length, bytes: m.total, missing, byCategory: m.byCategory };
  });
}

// Throttled static server for the first-load measurement. A shared token bucket caps the whole
// link at `bytesPerSec` (all connections together, service worker fetches included), which
// DevTools throttling does not do for service worker requests. gzip: true sends gzip -6 bodies.
async function startThrottledServer(port, bytesPerSec, gzipOn) {
  const http = await import('node:http');
  const zlib = await import('node:zlib');
  const { existsSync, statSync } = await import('node:fs');
  const DIST = path.join(APP, 'dist');
  const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.wasm': 'application/wasm', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webmanifest': 'application/manifest+json', '.onnx': 'application/octet-stream', '.mp3': 'audio/mpeg' };
  let nextFree = Date.now();
  const CHUNK = 16384;
  let sent = 0;
  const server = http.createServer(async (req, res) => {
    let rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (rel.endsWith('/')) rel += 'index.html';
    const file = path.join(DIST, rel);
    if (!file.startsWith(DIST) || !existsSync(file) || statSync(file).isDirectory()) {
      res.writeHead(404).end();
      return;
    }
    let body = readFileSync(file);
    const headers = { 'Content-Type': TYPES[path.extname(file)] ?? 'application/octet-stream', 'Cache-Control': 'no-cache' };
    if (gzipOn && /gzip/.test(req.headers['accept-encoding'] ?? '') && !/\.(png|jpg|mp3)$/.test(file)) {
      body = zlib.gzipSync(body, { level: 6 });
      headers['Content-Encoding'] = 'gzip';
    }
    headers['Content-Length'] = body.length;
    res.writeHead(200, headers);
    for (let i = 0; i < body.length; i += CHUNK) {
      const piece = body.subarray(i, i + CHUNK);
      const now = Date.now();
      const start = Math.max(now, nextFree);
      nextFree = start + (piece.length / bytesPerSec) * 1000;
      if (nextFree > now) await new Promise((r) => setTimeout(r, nextFree - now));
      if (res.destroyed) return;
      res.write(piece);
      sent += piece.length;
    }
    res.end();
  });
  await new Promise((r) => server.listen(port, '127.0.0.1', r));
  return { url: `http://127.0.0.1:${port}/`, close: () => server.close(), sent: () => sent };
}

async function measureFirstLoad(browser, gzipOn, port) {
  const bytesPerSec = 125000; // 1 Mbit/s, no protocol overhead (assumption)
  const srv = await startThrottledServer(port, bytesPerSec, gzipOn);
  const ctx = await browser.newContext({ viewport: { width: 360, height: 740 } });
  const page = await ctx.newPage();
  const t0 = Date.now();
  const out = { link: '1 Mbit/s shared, no added latency (assumption)', bytesPerSec, gzip: gzipOn, firstScreenMs: null, offlineReadyMs: null };
  try {
    await page.goto(srv.url, { waitUntil: 'commit', timeout: 120000 });
    await page.getByTestId('screen-language').waitFor({ timeout: 120000 });
    out.firstScreenMs = Date.now() - t0;
    out.bytesAtFirstScreen = srv.sent();
    note(`throttled (gzip=${gzipOn}): first screen after ${out.firstScreenMs} ms`);
    await page.waitForFunction(() => window.__janiOffline && window.__janiOffline.ready === true, null, { timeout: 400000, polling: 1000 });
    out.offlineReadyMs = Date.now() - t0;
    out.bytesTotal = srv.sent();
    note(`throttled (gzip=${gzipOn}): offline ready after ${out.offlineReadyMs} ms, ${out.bytesTotal} bytes on the wire`);
  } catch (e) {
    out.error = String(e).split('\n')[0];
    note(`throttled (gzip=${gzipOn}): ${out.error}`);
  }
  await ctx.close();
  srv.close();
  return out;
}

const FORBIDDEN = /phoma|cercospora|miner/i;

async function main() {
  if (!BASE) BASE = await startPreview();
  note(`base ${BASE}`);
  const browser = await launch();
  const result = { base: BASE, viewport: '360x740', steps: [], ok: false };
  try {
    const ctx = await browser.newContext({ viewport: { width: 360, height: 740 }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    const consoleLines = [];
    page.on('console', (m) => consoleLines.push(`${m.type()}: ${m.text()}`));

    const t0 = Date.now();
    await page.goto(BASE);
    await page.getByTestId('screen-language').waitFor();
    result.onlineFirstScreenMs = Date.now() - t0;
    await shot(page, 'online-language');

    const cache = await waitOfflineReady(page, 120000);
    result.precache = cache;
    note(`precache ok=${cache.ok} files=${cache.files} bytes=${cache.bytes} missing=${(cache.missing ?? []).length}`);
    if (!cache.ok) throw new Error('precache incomplete');

    await ctx.setOffline(true);
    await page.reload();
    await page.getByTestId('screen-language').waitFor({ timeout: 15000 });
    result.offlineReload = true;
    note('offline reload rendered the language screen');
    await shot(page, 'offline-language');

    await page.getByTestId('lang-en').click();
    // Consent is skipped when it was already given on this phone.
    if (await page.getByTestId('screen-consent').isVisible().catch(() => false)) {
      await shot(page, 'offline-consent');
      await page.getByTestId('consent-yes').click();
    }
    await page.getByTestId('screen-guide-pick').waitFor();
    await shot(page, 'offline-guide-pick');
    await page.getByTestId('guide-next').click();
    await page.getByTestId('screen-guide-photo').waitFor();
    await shot(page, 'offline-guide-photo');
    await page.getByTestId('guide-next').click();
    await page.getByTestId('screen-capture').waitFor();
    await shot(page, 'offline-capture-empty');

    const tClassify = Date.now();
    await page.getByTestId('sample-plot').click();
    await page.waitForFunction(() => !document.querySelector('[data-testid="busy"]') && document.querySelector('[data-testid="leaf-count"]'), null, {
      timeout: 180000,
      polling: 250,
    });
    // Wait until busy appeared and cleared (sample loading starts async).
    await page.waitForFunction(
      () => {
        const busy = document.querySelector('[data-testid="busy"]');
        const n = Number(document.querySelector('[data-testid="leaf-count"]')?.getAttribute('data-count') ?? 0);
        const r = document.querySelectorAll('[data-retake]').length;
        return !busy && n + r > 0;
      },
      null,
      { timeout: 180000, polling: 250 },
    );
    result.samplePlotMs = Date.now() - tClassify;
    const accepted = Number(await page.getByTestId('leaf-count').getAttribute('data-count'));
    const retakes = await page.$$eval('[data-retake]', (els) => els.map((e) => e.getAttribute('data-retake')));
    result.sample = { accepted, retakes };
    note(`sample plot: ${accepted} accepted, retakes ${JSON.stringify(retakes)} in ${result.samplePlotMs} ms`);
    result.mockBadge = await page.getByTestId('mock-badge').isVisible().catch(() => false);
    note(`mock badge visible: ${result.mockBadge}`);
    await shot(page, 'offline-capture-sample');
    result.leafResults = await page.evaluate(() => window.__janiResults ?? []);
    if (accepted + retakes.length === 0) throw new Error('no sample photo processed');

    await page.getByTestId('see-result').click();
    await page.getByTestId('screen-summary').waitFor();
    result.tiles = await page.$$eval('[data-group]', (els) => Object.fromEntries(els.map((e) => [e.getAttribute('data-group'), Number(e.getAttribute('data-count'))])));
    note(`summary tiles ${JSON.stringify(result.tiles)}`);
    await shot(page, 'offline-summary');

    await page.getByTestId('summary-next').click();
    await page.getByTestId('screen-answer').waitFor();
    result.answerId = await page.getByTestId('answer-card').getAttribute('data-card');
    result.berriesShown = await page.getByTestId('berries-card').isVisible();
    note(`answer ${result.answerId}, berries line shown: ${result.berriesShown}`);
    await shot(page, 'offline-answer');

    await page.getByTestId('answer-next').click();
    await page.getByTestId('screen-decision').waitFor();
    result.reachedDecision = true;
    await shot(page, 'offline-decision');

    await page.getByTestId('decide-ask').click();
    await page.getByTestId('screen-referral').waitFor();
    result.sms = await page.getByTestId('sms-preview').locator('code').innerText();
    note(`referral SMS (${result.sms.length} chars): ${result.sms}`);
    await shot(page, 'offline-referral');

    await page.getByTestId('referral-done').click();
    await page.getByTestId('screen-history').waitFor();
    await page.locator('.history-item').first().waitFor({ timeout: 10000 }).catch(() => undefined);
    result.historyItems = await page.locator('.history-item').count();
    note(`history items: ${result.historyItems}`);
    await shot(page, 'offline-history');

    // Camera path, still offline: one photo that fails opens its own retake screen.
    await page.getByRole('button', { name: /New check/ }).click();
    await page.getByTestId('screen-capture').waitFor();
    await page.getByTestId('camera-input').setInputFiles(path.join(APP, 'public', 'demo', 'sample12_poor.jpg'));
    await page.waitForFunction(() => document.querySelector('[data-testid="screen-retake"]') || Number(document.querySelector('[data-testid="leaf-count"]')?.getAttribute('data-count') ?? 0) > 0, null, { timeout: 60000 });
    result.cameraRetakeScreen = await page.getByTestId('screen-retake').isVisible().catch(() => false);
    result.cameraRetakeCard = result.cameraRetakeScreen ? await page.locator('[data-card]').first().getAttribute('data-card') : null;
    note(`camera photo (sample12_poor): retake screen ${result.cameraRetakeScreen}, card ${result.cameraRetakeCard}`);
    await shot(page, 'offline-camera-retake');
    if (result.cameraRetakeScreen) {
      await page.getByTestId('skip').click();
      await page.getByTestId('screen-capture').waitFor();
    }
    // Upload path (no camera): two photos at once.
    await page.getByTestId('upload-input').setInputFiles([
      path.join(APP, 'public', 'demo', 'sample11_berry.jpg'),
      path.join(APP, 'public', 'demo', 'sample09_healthy.jpg'),
    ]);
    await page.waitForFunction(() => !document.querySelector('[data-testid="busy"]') && (document.querySelectorAll('[data-retake]').length > 0 || Number(document.querySelector('[data-testid="leaf-count"]')?.getAttribute('data-count') ?? 0) > 0), null, { timeout: 60000 });
    result.upload = {
      accepted: Number(await page.getByTestId('leaf-count').getAttribute('data-count')),
      retakes: await page.$$eval('[data-retake]', (els) => els.map((e) => e.getAttribute('data-retake'))),
    };
    note(`upload of 2 photos: ${JSON.stringify(result.upload)}`);
    await shot(page, 'offline-upload');

    // Every farmer screen visited: no fine disease names.
    const seen = (await page.evaluate(() => document.body.innerText)) + '';
    result.forbiddenOnLastScreen = FORBIDDEN.test(seen);

    result.modelConsole = consoleLines.filter((l) => /\[model\]/.test(l));
    result.ok = result.reachedDecision === true && cache.ok && !result.forbiddenOnLastScreen && result.historyItems > 0;
    await ctx.close();

    if (process.env.MEASURE === '1') {
      result.firstLoad1Mbit = {
        gzip: await measureFirstLoad(browser, true, PORT + 10),
        raw: await measureFirstLoad(browser, false, PORT + 11),
      };
    }
  } catch (e) {
    result.error = String(e);
    note(`FAILED: ${String(e).split('\n')[0]}`);
  } finally {
    await browser.close();
    if (server) server.kill();
  }
  result.log = log;
  writeFileSync(path.join(SCREENS, 'result.json'), JSON.stringify(result, null, 2));
  const manifest = JSON.parse(readFileSync(path.join(APP, 'dist', 'precache-manifest.json'), 'utf8'));
  note(`precache total ${manifest.total} bytes, version ${manifest.version}`);
  console.log(result.ok ? 'E2E PASS' : 'E2E FAIL');
  process.exit(result.ok ? 0 : 1);
}

main();

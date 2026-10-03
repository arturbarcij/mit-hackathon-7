import { expect, test, type Page } from '@playwright/test';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

/*
 * Runs the engine in a real browser: service worker precache, onnxruntime-web (WASM, one thread),
 * then airplane mode and a full ten-leaf check. The harness stages the tiny fixture model unless
 * public/model has the real one. See tests/harness/build.mjs.
 */

const repoRoot = process.cwd();
const fixture = JSON.parse(readFileSync(join(repoRoot, 'tests', 'fixtures', 'model', 'expected.json'), 'utf8')) as { logits: number[] };
const usingRealModel = existsSync(join(repoRoot, 'public', 'model', 'leaf.onnx'));

async function waitForServiceWorker(page: Page) {
  await page.evaluate(async () => {
    const reg = await navigator.serviceWorker.ready;
    if (!reg.active) throw new Error('no active service worker');
  });
  // Reload once so the page is controlled and the precache has finished installing.
  await page.reload();
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null);
}

test('service worker precaches the model, WASM runtime and app', async ({ page }) => {
  await page.goto('/');
  await waitForServiceWorker(page);
  const cached = await page.evaluate(async () => {
    const urls: string[] = [];
    for (const name of await caches.keys()) {
      const c = await caches.open(name);
      for (const r of await c.keys()) urls.push(new URL(r.url).pathname);
    }
    return urls;
  });
  expect(cached.some((u) => u.endsWith('/model/leaf.onnx'))).toBe(true);
  expect(cached.some((u) => u.endsWith('/model/model.json'))).toBe(true);
  expect(cached.some((u) => u.endsWith('ort-wasm-simd-threaded.wasm'))).toBe(true);
  expect(cached.some((u) => u.endsWith('ort-wasm-simd-threaded.mjs'))).toBe(true);
});

test('real ONNX runtime matches onnxruntime (Python) on the reference tensor', async ({ page }) => {
  test.skip(usingRealModel, 'reference logits belong to the fixture model');
  await page.goto('/');
  await page.waitForFunction(() => (window as any).__jani?.ready);
  const probs = await page.evaluate(() => (window as any).__jani.referenceProbs() as Promise<Record<string, number>>);
  const logits = fixture.logits;
  const max = Math.max(...logits);
  const exps = logits.map((l) => Math.exp(l - max));
  const sum = exps.reduce((a, b) => a + b, 0);
  const expected = exps.map((e) => e / sum);
  const labels = ['healthy', 'rust', 'cercospora', 'phoma', 'miner', 'not_leaf'];
  labels.forEach((l, i) => expect(Math.abs(probs[l] - expected[i])).toBeLessThan(1e-4));
});

test('full ten-leaf check works in airplane mode', async ({ page, context }) => {
  test.skip(usingRealModel, 'colour-based expectations belong to the fixture model');
  await page.goto('/');
  await waitForServiceWorker(page);

  await context.setOffline(true);
  await page.reload();
  await page.waitForFunction(() => (window as any).__jani?.ready);

  const out = await page.evaluate(async () => {
    const j = (window as any).__jani;
    const e = j.engine;
    const model = await e.loadModel();
    const specs: [string, [number, number, number]][] = [];
    for (let i = 0; i < 6; i++) specs.push([`rust_${i}.jpg`, [190, 60, 50]]);
    for (let i = 0; i < 3; i++) specs.push([`healthy_${i}.jpg`, [50, 160, 60]]);
    specs.push(['unclear.jpg', [120, 120, 120]]);
    const leaves = [];
    const times: number[] = [];
    for (const [name, rgb] of specs) {
      const file = await j.makeLeafFile(name, rgb);
      const t0 = performance.now();
      leaves.push(await e.classifyFile(file));
      times.push(performance.now() - t0);
    }
    const blurry = await e.classifyFile(await j.makeLeafFile('blur.jpg', [100, 140, 90], { texture: 0 }));
    const tiny = await e.classifyFile(await j.makeLeafFile('tiny.jpg', [100, 140, 90], { width: 120, height: 120 }));
    const dark = await e.classifyFile(await j.makeLeafFile('dark.jpg', [8, 12, 8], { texture: 6 }));

    const check = e.assembleCheck({ leaves, lang: 'sw', date: new Date(2026, 9, 4, 10), memberId: 'OCC0412', plotId: '2', consentMain: true, consentPhotos: false });
    check.decision = 'ask';
    await e.saveCheck(check);
    const saved = await e.listChecks();
    return {
      model,
      labels: leaves.map((l: any) => l.label),
      summary: check.summary,
      answerId: check.answerId,
      window: check.window,
      sms: e.buildReferral(check),
      parsed: e.parseReferral(e.buildReferral(check)),
      savedIds: saved.map((c: any) => c.id),
      checkId: check.id,
      quality: { blurry: blurry.quality, tiny: tiny.quality, dark: dark.quality, blurryLabel: blurry.label },
      maxMs: Math.max(...times),
      networkReachable: await fetch('/not-in-the-precache.txt?' + Date.now()).then(() => true, () => false),
    };
  });

  expect(out.networkReachable).toBe(false);
  expect(out.model.mock).toBe(false);
  expect(out.labels.slice(0, 6)).toEqual(Array(6).fill('rust'));
  expect(out.labels.slice(6, 9)).toEqual(Array(3).fill('healthy'));
  expect(out.labels[9]).toBe('unsure');
  expect(out.summary.counts.rust).toBe(6);
  expect(out.summary.uncertain).toBe(1);
  expect(out.window).toBe('pre_short_rains');
  expect(out.answerId).toBe('rust_high_pre_rains');
  expect(out.sms.length).toBeLessThanOrEqual(160);
  expect(out.parsed.rust).toBe(6);
  expect(out.savedIds).toContain(out.checkId);
  expect(out.quality.blurry.reason).toBe('blurry');
  expect(out.quality.blurryLabel).toBe('unsure');
  expect(out.quality.tiny.reason).toBe('too_small');
  expect(out.quality.dark.reason).toBe('dark');
  console.log(`slowest leaf (decode + quality + inference) in this run: ${Math.round(out.maxMs)} ms`);
});

test('inference timing with the CPU throttled 4x (logged for kb/STATUS.md)', async ({ page }) => {
  await page.goto('/');
  await page.waitForFunction(() => (window as any).__jani?.ready);
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  const t = await page.evaluate(async () => {
    const j = (window as any).__jani;
    const t0 = performance.now();
    await j.engine.loadModel();
    const loadMs = performance.now() - t0;
    const runs: number[] = [];
    for (let i = 0; i < 5; i++) {
      const file = await j.makeLeafFile(`rust_${i}.jpg`, [190, 60, 50], { width: 3000, height: 2250 });
      const s = performance.now();
      await j.engine.classifyFile(file);
      runs.push(performance.now() - s);
    }
    return { loadMs, runs, inferMs: j.engine.lastInferenceTimeMs() };
  });
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 });
  console.log(`4x throttle: model load ${Math.round(t.loadMs)} ms; per photo (3000x2250 decode + quality + preprocess + inference) ${t.runs.map((r) => Math.round(r)).join(', ')} ms; last inference only ${t.inferMs.toFixed(1)} ms; model is ${usingRealModel ? 'REAL' : 'the fixture, not a coffee model'}`);
  expect(Math.min(...t.runs)).toBeLessThan(1000);
});

test('real model: parity samples match when present', async ({ page }) => {
  const dir = join(repoRoot, 'ml', 'parity_samples');
  test.skip(!usingRealModel || !existsSync(dir), 'needs public/model and ml/parity_samples (from the ml agent)');
  const expectedPath = join(dir, 'expected.json');
  test.skip(!existsSync(expectedPath), 'ml/parity_samples/expected.json missing');
  const expected = JSON.parse(readFileSync(expectedPath, 'utf8')) as Record<string, { label: string; probs: Record<string, number> }>;
  const files = readdirSync(dir).filter((f) => /\.(jpe?g|png)$/i.test(f));
  expect(files.length).toBeGreaterThan(0);
  await page.goto('/');
  await page.waitForFunction(() => (window as any).__jani?.ready);
  for (const f of files) {
    const bytes = readFileSync(join(dir, f)).toString('base64');
    const res = await page.evaluate(async ([name, b64]) => {
      const bin = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
      const file = new File([bin], name, { type: name.endsWith('png') ? 'image/png' : 'image/jpeg' });
      return (window as any).__jani.engine.classifyFile(file);
    }, [f, bytes]);
    const want = expected[f];
    expect(want, f).toBeDefined();
    for (const [label, p] of Object.entries(want.probs)) expect(Math.abs(res.probs[label] - p), `${f} ${label}`).toBeLessThan(0.02);
  }
});

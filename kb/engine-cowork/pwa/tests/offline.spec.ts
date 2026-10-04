import { test, expect, chromium, type Page, type BrowserContext } from '@playwright/test'
import { spawn, type ChildProcess } from 'node:child_process'
import { writeFileSync, statSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const PORT = 3177
const BASE = `http://127.0.0.1:${PORT}`
const OUT = join(process.cwd(), '.output')

function startServer(): Promise<ChildProcess> {
  return new Promise((resolve, reject) => {
    const p = spawn('node', [join(OUT, 'server/index.mjs')], {
      env: { ...process.env, PORT: String(PORT), HOST: '127.0.0.1' },
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    const t = setTimeout(() => reject(new Error('server did not start')), 15_000)
    const tryFetch = async () => {
      try {
        const r = await fetch(BASE + '/')
        if (r.ok) { clearTimeout(t); resolve(p) } else setTimeout(tryFetch, 200)
      } catch { setTimeout(tryFetch, 200) }
    }
    setTimeout(tryFetch, 300)
    p.on('exit', (c) => { if (c !== 0 && c !== null) reject(new Error('server exited ' + c)) })
  })
}

async function waitForPrecache(page: Page) {
  await page.waitForFunction(() => navigator.serviceWorker?.controller != null, null, { timeout: 60_000 })
  // Wait until the precache cache holds every entry listed in sw.js.
  await page.waitForFunction(async () => {
    const sw = await (await fetch('/sw.js')).text()
    const urls = [...sw.matchAll(/url:"([^"]+)"/g)].map((m) => m[1])
    const keys = await caches.keys()
    const pre = keys.find((k) => k.includes('precache'))
    if (!pre) return false
    const c = await caches.open(pre)
    const have = (await c.keys()).map((r) => new URL(r.url).pathname)
    return urls.every((u) => have.some((h) => h === '/' + u))
  }, null, { timeout: 120_000 })
}

async function measureCache(page: Page) {
  return page.evaluate(async () => {
    const keys = await caches.keys()
    const out: Record<string, { entries: number; bytes: number; urls: Record<string, number> }> = {}
    for (const k of keys) {
      const c = await caches.open(k)
      const reqs = await c.keys()
      let bytes = 0
      const urls: Record<string, number> = {}
      for (const r of reqs) {
        const res = await c.match(r)
        const b = res ? (await res.arrayBuffer()).byteLength : 0
        bytes += b
        urls[new URL(r.url).pathname] = b
      }
      out[k] = { entries: reqs.length, bytes, urls }
    }
    return out
  })
}

async function clickRun(page: Page) {
  await page.click('#run')
  await page.waitForFunction(() => {
    const t = document.querySelector('#out')?.textContent ?? ''
    return t.startsWith('{') && t.includes('"ok"')
  }, null, { timeout: 120_000 })
  return JSON.parse((await page.textContent('#out'))!)
}

test('TanStack Start PWA: precache, offline reload, ONNX inference', async () => {
  const server = await startServer()
  const browser = await chromium.launch()
  const context: BrowserContext = await browser.newContext({ viewport: { width: 360, height: 740 } })
  const page = await context.newPage()

  const failed: string[] = []
  const requested: { url: string; fromSW: boolean }[] = []
  page.on('requestfailed', (r) => failed.push(r.url() + ' ' + (r.failure()?.errorText ?? '')))
  page.on('requestfinished', async (r) => {
    const res = await r.response()
    requested.push({ url: new URL(r.url()).pathname, fromSW: res?.fromServiceWorker() ?? false })
  })
  const consoleLines: string[] = []
  page.on('console', (m) => consoleLines.push(m.type() + ': ' + m.text()))

  // 1. Online visit: SW registers and precaches everything.
  await page.goto(BASE + '/')
  await waitForPrecache(page)
  const cacheOnline = await measureCache(page)
  // Also run once online to warm nothing; the SW already has everything.
  const onlineResult = await clickRun(page)
  expect(onlineResult.ok).toBe(true)

  // 2. Offline: reload and run.
  await context.setOffline(true)
  failed.length = 0
  requested.length = 0
  await page.reload()
  await page.waitForSelector('#run')
  const offlineResult = await clickRun(page)
  expect(offlineResult.ok).toBe(true)
  expect(typeof offlineResult.argmax).toBe('number')
  expect(offlineResult.modelVersion).toMatch(/^test-/)
  expect(offlineResult.online).toBe(false)
  expect(offlineResult.swControlled).toBe(true)
  expect(offlineResult.onnxBytes).toBeGreaterThan(1_000_000)
  expect(offlineResult.mp3Bytes).toBeGreaterThan(1000)
  expect(offlineResult.answersBytes).toBeGreaterThan(1000)
  expect(failed, 'no failed requests while offline').toEqual([])
  const offlineRequests = requested.slice()
  expect(offlineRequests.every((r) => r.fromSW), 'every offline request served by SW').toBe(true)

  // 3. Throttled: CDP 4x CPU throttle, still offline.
  const cdp = await context.newCDPSession(page)
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 })
  const throttled = await clickRun(page)
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 })
  expect(throttled.ok).toBe(true)
  expect(throttled.argmax).toBe(offlineResult.argmax)

  // 4. Server killed, context back "online" (network up but origin dead): must still work.
  server.kill('SIGKILL')
  await new Promise((r) => setTimeout(r, 500))
  await context.setOffline(false)
  failed.length = 0
  await page.reload()
  await page.waitForSelector('#run')
  const deadServerResult = await clickRun(page)
  expect(deadServerResult.ok).toBe(true)
  expect(deadServerResult.argmax).toBe(offlineResult.argmax)
  // Workbox NetworkFirst for navigations tries the network first; with the server dead that
  // attempt fails (recorded as a failed request) and the cached page is served. Assets come
  // from the precache without touching the network.
  const nonNavFailures = failed.filter((f) => !f.startsWith(BASE + '/ ') && !f.startsWith(BASE + '/?'))
  expect(nonNavFailures, 'only the navigation probe may fail with a dead server').toEqual([])

  const files = (dir: string, prefix = ''): Record<string, number> =>
    Object.fromEntries(
      readdirSync(join(dir, prefix), { withFileTypes: true }).flatMap((d) =>
        d.isDirectory() ? Object.entries(files(dir, join(prefix, d.name))) : [[join(prefix, d.name), statSync(join(dir, prefix, d.name)).size]],
      ),
    )
  const pub = files(join(OUT, 'public'))
  const wasmFiles = Object.fromEntries(Object.entries(pub).filter(([k]) => k.endsWith('.wasm')))
  const precacheKey = Object.keys(cacheOnline).find((k) => k.includes('precache'))!

  const results = {
    stack: 'TanStack Start (@tanstack/react-start 1.168.60, vite 8.1.5, nitro 3.0.260603-beta node-server preset) + @lovable.dev/vite-tanstack-config 2.25.1 + vite-plugin-pwa 1.3.0 + workbox-build in client closeBundle',
    proven: {
      serviceWorkerRegistered: true,
      precacheComplete: true,
      offlineReloadAndInference: offlineResult.ok,
      throttledInference: throttled.ok,
      deadServerReloadAndInference: deadServerResult.ok,
      allOfflineRequestsFromServiceWorker: offlineRequests.every((r) => r.fromSW),
    },
    sizes: {
      precacheEntries: cacheOnline[precacheKey].entries,
      precacheBytes: cacheOnline[precacheKey].bytes,
      precacheMB: +(cacheOnline[precacheKey].bytes / 1024 / 1024).toFixed(2),
      onnxBytes: offlineResult.onnxBytes,
      wasmFiles,
      mp3Bytes: offlineResult.mp3Bytes,
      answersJsonBytes: offlineResult.answersBytes,
      perUrl: cacheOnline[precacheKey].urls,
      otherCaches: Object.fromEntries(Object.entries(cacheOnline).filter(([k]) => k !== precacheKey).map(([k, v]) => [k, { entries: v.entries, bytes: v.bytes }])),
    },
    timings: {
      online: { fetchMs: onlineResult.fetchMs, sessionCreateMs: onlineResult.sessionCreateMs, inferMs: onlineResult.inferMs },
      offline: { fetchMs: offlineResult.fetchMs, sessionCreateMs: offlineResult.sessionCreateMs, inferMs: offlineResult.inferMs },
      offlineCpuThrottle4x: { fetchMs: throttled.fetchMs, sessionCreateMs: throttled.sessionCreateMs, inferMs: throttled.inferMs },
      deadServer: { fetchMs: deadServerResult.fetchMs, sessionCreateMs: deadServerResult.sessionCreateMs, inferMs: deadServerResult.inferMs },
    },
    inference: { argmax: offlineResult.argmax, numClasses: offlineResult.numClasses, modelVersion: offlineResult.modelVersion, logits: offlineResult.logits },
    offlineRequests: offlineRequests,
    console: consoleLines.slice(0, 40),
  }
  writeFileSync(join(process.cwd(), '..', 'RESULTS.raw.json'), JSON.stringify(results, null, 2))
  await browser.close()
})

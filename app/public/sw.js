/* Jani service worker for the static farmer PWA. Hand-written, no Workbox.
 * Follows kb/engine-cowork/pwa/RECIPE.md. Precache list and version come from
 * precache-manifest.js, written at build time by the jani-precache plugin in vite.config.ts.
 * - install: cache the app shell and every file in the manifest; install fails if any file fails,
 *   so an active worker means the whole app is on the phone.
 * - activate: delete older jani-* caches, take control of open pages.
 * - navigations: network first (3 s timeout), then the cached shell.
 * - precached URLs: cache first.
 * - everything else: straight to the network, never cached.
 */
importScripts('precache-manifest.js');
const M = self.__JANI_PRECACHE;
const CACHE = 'jani-precache-' + M.version;
const SHELL = M.shell[0];
const PRECACHED = new Set(M.files.map((f) => f.url).concat(M.shell));
const NAV_TIMEOUT_MS = 3000;

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      const urls = M.shell.concat(M.files.map((f) => f.url));
      await cache.addAll(urls.map((u) => new Request(u, { cache: 'reload' })));
      await self.skipWaiting();
    })(),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k.startsWith('jani-') && k !== CACHE).map((k) => caches.delete(k)));
      await self.clients.claim();
    })(),
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'jani-status') {
    const reply = { type: 'jani-status', version: M.version, files: M.files.length, bytes: M.total };
    if (event.ports && event.ports[0]) event.ports[0].postMessage(reply);
    else if (event.source) event.source.postMessage(reply);
  }
});

function timeout(ms) {
  return new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms));
}

async function navigate(request) {
  const cache = await caches.open(CACHE);
  try {
    // Do not refresh the cached shell here: a newer HTML could point at assets this cache lacks.
    return await Promise.race([fetch(request), timeout(NAV_TIMEOUT_MS)]);
  } catch (e) {
    return (await cache.match(request, { ignoreSearch: true })) || (await cache.match(SHELL)) || Response.error();
  }
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (req.mode === 'navigate') {
    event.respondWith(navigate(req));
    return;
  }
  if (PRECACHED.has(url.pathname)) {
    event.respondWith(caches.open(CACHE).then((c) => c.match(url.pathname).then((hit) => hit || fetch(req))));
  }
});

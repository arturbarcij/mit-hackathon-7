// Mirror of the Lovable TanStack Start project, plus PWA.
// The Lovable preset adds: tailwindcss(), tsconfigPaths(), tanstackStart(), nitro() (build only), viteReact().
// User plugins passed in `plugins` are appended AFTER those internal plugins.
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'
import { defineConfig } from '@lovable.dev/vite-tanstack-config'
import type { Plugin } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

const PRECACHE_GLOBS = ['**/*.{js,css,html,svg,png,ico,json,onnx,wasm,mp3,webmanifest}']
const MAX_FILE = 15 * 1024 * 1024
const PRECACHE_EXT = /\.(js|css|html|svg|png|ico|json|onnx|wasm|mp3|webmanifest)$/

function listFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((d) => (d.isDirectory() ? listFiles(join(dir, d.name)) : [join(dir, d.name)]))
}

// vite-plugin-pwa's own generateSW step does not fit TanStack Start + nitro: it globs the root
// outDir (dist), while the client bundle is written to the client environment's outDir, which nitro
// redirects to .output/public (node-server preset). Nitro then bakes a public-asset manifest for the
// node server, so a sw.js written later (for example from a buildApp hook) is served as 404.
// The fix is a per-environment closeBundle hook: it runs when the client environment has finished
// writing (public/ copied, assets emitted) and before nitro scans the folder.
function workboxClientEnv(): Plugin {
  return {
    name: 'jani:workbox-client-env',
    apply: 'build',
    enforce: 'post',
    async closeBundle() {
      if (this.environment?.name !== 'client') return
      const publicDir = resolve(process.cwd(), this.environment.config.build.outDir)
      // Nitro copies the project's public/ folder into the output itself, after this hook, so
      // public/ files (model, audio, content, icons) are not on disk yet. Add them to the precache
      // manifest directly from public/, with a content hash as revision.
      const projectPublic = resolve(process.cwd(), 'public')
      const additionalManifestEntries = listFiles(projectPublic)
        .filter((f) => PRECACHE_EXT.test(f))
        .map((f) => ({
          url: relative(projectPublic, f).split('\\').join('/'),
          revision: createHash('md5').update(readFileSync(f)).digest('hex'),
          size: statSync(f).size,
        }))
      const publicBytes = additionalManifestEntries.reduce((a, e) => a + e.size, 0)
      const { generateSW } = await import('workbox-build')
      const { count, size, warnings } = await generateSW({
        swDest: join(publicDir, 'sw.js'),
        globDirectory: publicDir,
        globPatterns: PRECACHE_GLOBS,
        globIgnores: ['sw.js', 'workbox-*.js', '**/*.map'],
        additionalManifestEntries: additionalManifestEntries.map(({ url, revision }) => ({ url, revision })),
        maximumFileSizeToCacheInBytes: MAX_FILE,
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true,
        // SSR app: no index.html. Cache the HTML of every navigation on first visit and serve it
        // from cache when offline. The precached assets then make the page work without a server.
        navigateFallback: undefined,
        runtimeCaching: [
          {
            urlPattern: ({ request }) => request.mode === 'navigate',
            handler: 'NetworkFirst',
            options: { cacheName: 'jani-pages', networkTimeoutSeconds: 3 },
          },
        ],
      })
      for (const w of warnings) console.warn('[workbox]', w)
      console.log(
        `[jani:workbox-client-env] ${count} built files (${(size / 1024 / 1024).toFixed(2)} MB) + ${additionalManifestEntries.length} public/ files (${(publicBytes / 1024 / 1024).toFixed(2)} MB) precached -> ${publicDir}/sw.js`,
      )
    },
  }
}

export default defineConfig({
  plugins: [
    VitePWA({
      // Used for: manifest.webmanifest, `virtual:pwa-register` (workbox-window) and types.
      // Its own sw.js (written to dist/) is unused; workboxClientEnv() writes the real one.
      registerType: 'autoUpdate',
      injectRegister: false, // no index.html to inject into; we register in src/routes/__root.tsx
      filename: 'sw.js',
      manifestFilename: 'manifest.webmanifest',
      manifest: {
        name: 'Jani',
        short_name: 'Jani',
        description: 'Coffee leaf check that works offline',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#ffffff',
        theme_color: '#2f6b3a',
        lang: 'sw',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        globPatterns: PRECACHE_GLOBS,
        maximumFileSizeToCacheInBytes: MAX_FILE,
      },
      devOptions: { enabled: false },
    }),
    workboxClientEnv(),
  ],
})

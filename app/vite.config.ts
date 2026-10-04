// Static farmer PWA (EDGE_PLAN move 3 fallback). Plain Vite + React, no server.
// The jani-precache plugin follows kb/engine-cowork/pwa/RECIPE.md:
// - lists every built asset plus public/model, public/ort, public/audio, public/demo, icons and
//   the web manifest, and writes /precache-manifest.json (for QA) and /precache-manifest.js
//   (read by public/sw.js with importScripts);
// - drops the duplicate onnxruntime wasm that Vite emits under assets/ (the engine loads it from /ort/);
// - if public/ort/ is missing, copies ort-wasm-simd-threaded.{wasm,mjs} from node_modules into
//   the build (and serves them in dev), so the real model can load without anyone committing 14 MB.
// It also exposes the list of recorded audio clips as __JANI_AUDIO__ so the speaker button
// knows when a clip exists.
import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig, type Plugin, type ResolvedConfig } from 'vite';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC = path.join(ROOT, 'public');
// Public folders the farmer flow needs offline. public/geo is officer-only and is not precached.
const PUBLIC_DIRS = ['model', 'ort', 'audio', 'demo', 'icons'];
const PUBLIC_FILES = ['manifest.webmanifest'];
const ORT_FILES = ['ort-wasm-simd-threaded.wasm', 'ort-wasm-simd-threaded.mjs'];
const ORT_DIST = path.join(ROOT, 'node_modules', 'onnxruntime-web', 'dist');

function walk(dir: string, base: string, out: string[]): void {
  if (!existsSync(dir)) return;
  for (const name of readdirSync(dir)) {
    const p = path.join(dir, name);
    if (statSync(p).isDirectory()) walk(p, base, out);
    else out.push(path.relative(base, p).split(path.sep).join('/'));
  }
}

function audioClips(): string[] {
  const files: string[] = [];
  walk(path.join(PUBLIC, 'audio'), path.join(PUBLIC, 'audio'), files);
  return files.filter((f) => f.endsWith('.mp3')).map((f) => f.replace(/\.mp3$/, '')).sort();
}

function needOrtCopy(): boolean {
  return !ORT_FILES.every((f) => existsSync(path.join(PUBLIC, 'ort', f)));
}

function janiPrecache(): Plugin {
  let config: ResolvedConfig;
  return {
    name: 'jani-precache',
    configResolved(c) {
      config = c;
    },
    configureServer(server) {
      // Dev only: serve /ort/* from node_modules when public/ort is missing.
      if (!needOrtCopy()) return;
      server.middlewares.use((req, res, next) => {
        const m = /^\/ort\/([^?]+)/.exec(req.url ?? '');
        if (!m || !ORT_FILES.includes(m[1])) return next();
        res.setHeader('Content-Type', m[1].endsWith('.wasm') ? 'application/wasm' : 'text/javascript');
        res.end(readFileSync(path.join(ORT_DIST, m[1])));
      });
    },
    generateBundle(_opts, bundle) {
      if (config.command !== 'build') return;
      const base = config.base.endsWith('/') ? config.base : config.base + '/';
      const entries: { url: string; bytes: number; category: string }[] = [];
      for (const [fileName, item] of Object.entries(bundle)) {
        if (/^assets\/ort-wasm.*\.wasm$/.test(fileName)) {
          delete bundle[fileName];
          continue;
        }
        if (fileName.endsWith('.map') || fileName === 'index.html') continue;
        const bytes =
          item.type === 'chunk'
            ? Buffer.byteLength(item.code)
            : typeof item.source === 'string'
              ? Buffer.byteLength(item.source)
              : item.source.byteLength;
        const category = fileName.endsWith('.css') ? 'app_css' : fileName.endsWith('.js') ? 'app_js' : 'app_other';
        entries.push({ url: base + fileName, bytes, category });
      }
      if (needOrtCopy()) {
        for (const f of ORT_FILES) {
          const src = readFileSync(path.join(ORT_DIST, f));
          this.emitFile({ type: 'asset', fileName: `ort/${f}`, source: src });
          entries.push({ url: `${base}ort/${f}`, bytes: src.byteLength, category: 'ort' });
        }
      }
      const pub: string[] = [];
      for (const d of PUBLIC_DIRS) walk(path.join(PUBLIC, d), PUBLIC, pub);
      for (const f of PUBLIC_FILES) if (existsSync(path.join(PUBLIC, f))) pub.push(f);
      for (const f of pub) {
        const category = f.split('/').length > 1 ? f.split('/')[0] : 'shell';
        entries.push({ url: base + f, bytes: statSync(path.join(PUBLIC, f)).size, category });
      }
      entries.sort((a, b) => a.url.localeCompare(b.url));
      const hash = createHash('sha256');
      for (const e of entries) hash.update(`${e.url}:${e.bytes}\n`);
      for (const [fileName, item] of Object.entries(bundle)) {
        if (item.type === 'chunk') hash.update(fileName + item.code);
      }
      for (const f of pub) hash.update(readFileSync(path.join(PUBLIC, f)));
      const version = hash.digest('hex').slice(0, 12);
      const total = entries.reduce((s, e) => s + e.bytes, 0);
      const byCategory: Record<string, { files: number; bytes: number }> = {};
      for (const e of entries) {
        const c = (byCategory[e.category] ??= { files: 0, bytes: 0 });
        c.files += 1;
        c.bytes += e.bytes;
      }
      const manifest = { version, total, base, shell: [base], byCategory, files: entries.map(({ url, bytes }) => ({ url, bytes })) };
      this.emitFile({ type: 'asset', fileName: 'precache-manifest.json', source: JSON.stringify(manifest, null, 1) });
      // Netlify reads _headers from the published folder, so drag-and-drop deploys get these too.
      this.emitFile({
        type: 'asset',
        fileName: '_headers',
        source: [
          `${base}sw.js`,
          '  Cache-Control: no-cache',
          `${base}precache-manifest.js`,
          '  Cache-Control: no-cache',
          `${base}assets/*`,
          '  Cache-Control: public, max-age=31536000, immutable',
          `${base}ort/*`,
          '  Cache-Control: no-cache',
          '',
        ].join('\n'),
      });
      this.emitFile({
        type: 'asset',
        fileName: 'precache-manifest.js',
        source: `self.__JANI_PRECACHE = ${JSON.stringify(manifest)};\n`,
      });
    },
  };
}

// https://vite.dev/config/
// BASE: set to '/<repo>/' for a GitHub Pages project site (see README_DEPLOY.md).
export default defineConfig({
  base: process.env.BASE ?? '/',
  plugins: [react(), janiPrecache()],
  define: {
    __JANI_AUDIO__: JSON.stringify(audioClips()),
  },
  build: {
    // The onnxruntime wasm entry is about 400 kB; it is precached, so the warning is noise.
    chunkSizeWarningLimit: 1500,
  },
});

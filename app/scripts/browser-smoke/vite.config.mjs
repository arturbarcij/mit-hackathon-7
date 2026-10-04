// Scratch build of the engine for a headless-browser smoke test. Not the app build.
import { resolve } from 'node:path';
import { defineConfig } from 'vite';
const here = import.meta.dirname;
export default defineConfig({
  root: here,
  publicDir: resolve(here, '../../public'),
  build: { outDir: resolve(here, 'dist'), emptyOutDir: true },
});

import { join } from 'node:path'
import { defineConfig, mergeConfig } from 'vite'
import base from './vite.config.ts'

// Test-only build of tests/harness with the same PWA settings as the app. See tests/harness/build.mjs.
const work = join(import.meta.dirname, 'node_modules', '.jani-harness')

export default mergeConfig(
  base,
  defineConfig({
    root: join(import.meta.dirname, 'tests', 'harness'),
    publicDir: join(work, 'public'),
    build: { outDir: join(work, 'dist'), emptyOutDir: true },
  }),
)

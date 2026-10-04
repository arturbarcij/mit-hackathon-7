import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// The engine under test. Default is the reference implementation in ./reference.
// Override with ENGINE_PATH (absolute, or relative to this directory), pointing at a
// directory that has an index.ts (or a file). Example:
//   ENGINE_PATH=../_inputs/lovable/src/engine npx vitest run
//   ENGINE_PATH=/path/to/app/src/engine npx vitest run
const here = path.dirname(fileURLToPath(import.meta.url));
const enginePath = path.resolve(here, process.env.ENGINE_PATH ?? './reference');

export default defineConfig({
  resolve: {
    alias: {
      '@engine-under-test': enginePath,
    },
  },
  define: {
    __ENGINE_PATH__: JSON.stringify(enginePath),
  },
  test: {
    include: ['tests/**/*.test.ts'],
    environment: 'node',
    testTimeout: 60_000,
    reporters: process.env.CI ? ['default', 'junit'] : ['default'],
    outputFile: { junit: './_work/junit.xml' },
  },
});

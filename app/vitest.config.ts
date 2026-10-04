import { defineConfig } from 'vitest/config';

// Engine tests only. Pure logic runs in node; files that need a DOM declare
// `// @vitest-environment jsdom` at the top.
export default defineConfig({
  test: {
    include: ['tests/engine/**/*.test.ts', 'tests/engine/**/*.test.tsx'],
    environment: 'node',
    testTimeout: 20000,
  },
});

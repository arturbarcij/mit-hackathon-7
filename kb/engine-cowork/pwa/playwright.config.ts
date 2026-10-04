import { defineConfig } from '@playwright/test'

// Chromium comes from /opt/pw-browsers (PLAYWRIGHT_BROWSERS_PATH). Never run `playwright install` here.
// The server is started by the test itself (tests/offline.spec.ts) so that it can be killed mid-test.
export default defineConfig({
  testDir: './tests',
  timeout: 180_000,
  retries: 0,
  workers: 1,
  reporter: [['list'], ['json', { outputFile: '../pw-report.json' }]],
  use: {
    browserName: 'chromium',
    viewport: { width: 360, height: 740 },
    serviceWorkers: 'allow',
    trace: 'retain-on-failure',
  },
})

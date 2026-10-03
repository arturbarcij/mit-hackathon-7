import { defineConfig } from '@playwright/test'
import { existsSync } from 'node:fs'

const chrome = process.env.CHROME_PATH ?? (existsSync('/usr/local/bin/google-chrome') ? '/usr/local/bin/google-chrome' : undefined)

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 90_000,
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:4175',
    launchOptions: { executablePath: chrome, args: ['--no-sandbox'] },
  },
  webServer: {
    command: 'node tests/harness/build.mjs && npx vite preview --config vite.harness.config.ts --port 4175 --strictPort',
    url: 'http://localhost:4175',
    reuseExistingServer: false,
    timeout: 120_000,
  },
})

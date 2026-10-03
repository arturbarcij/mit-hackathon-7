// Shared helper for the real-photo evaluations: builds the harness, serves it, opens it in Chrome.
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { chromium } from '@playwright/test';

export async function openHarness(port = 4180) {
  await new Promise((resolve, reject) => {
    const b = spawn('node', ['tests/harness/build.mjs'], { stdio: 'inherit' });
    b.on('exit', (c) => (c === 0 ? resolve() : reject(new Error('harness build failed'))));
  });
  const server = spawn('npx', ['vite', 'preview', '--config', 'vite.harness.config.ts', '--port', String(port), '--strictPort'], { stdio: 'ignore' });
  for (let i = 0; i < 50; i++) {
    try { if ((await fetch(`http://localhost:${port}/`)).ok) break; } catch { /* not up yet */ }
    await new Promise((r) => setTimeout(r, 200));
  }
  const exe = process.env.CHROME_PATH ?? (existsSync('/usr/local/bin/google-chrome') ? '/usr/local/bin/google-chrome' : undefined);
  const browser = await chromium.launch({ executablePath: exe, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.goto(`http://localhost:${port}/`);
  await page.waitForFunction(() => window.__jani?.ready);
  return { page, close: async () => { await browser.close(); server.kill(); } };
}

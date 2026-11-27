import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests',
  expect: { timeout: 10000 },
  timeout: 60000,
  testIgnore: '**/screenshots.spec.ts',
  use: { baseURL: 'http://127.0.0.1:5173', viewport: { width: 1280, height: 800 }, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: [
    { command: 'uv run python -m app.cli serve', cwd: '..', url: 'http://127.0.0.1:8000/api/health/live', env: { APP_DATABASE: 'data/e2e.sqlite3' }, reuseExistingServer: false },
    { command: 'pnpm build && pnpm preview', url: 'http://127.0.0.1:5173', reuseExistingServer: false, timeout: 120000 },
  ],
});


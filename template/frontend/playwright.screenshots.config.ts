import { defineConfig } from '@playwright/test';
import base from './playwright.config';

export default defineConfig({
  ...base,
  testIgnore: [],
  testMatch: 'screenshots.spec.ts',
  fullyParallel: true,
  workers: 2,
  webServer: {
    command: 'task ui:serve',
    cwd: '..',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: false,
    timeout: 120000,
  },
  use: { ...base.use, deviceScaleFactor: 1, reducedMotion: 'reduce' },
});

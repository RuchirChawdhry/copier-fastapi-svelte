import { defineConfig } from '@playwright/test';
import base from './playwright.config';

export default defineConfig({
  ...base,
  testIgnore: [],
  testMatch: 'screenshots.spec.ts',
  workers: 1,
  fullyParallel: false,
  webServer: base.webServer && Array.isArray(base.webServer)
    ? base.webServer.map(server => server.env?.APP_DATABASE
      ? { ...server, env: { ...server.env, APP_DATABASE: 'data/screenshots.sqlite3' } }
      : server)
    : base.webServer,
  use: { ...base.use, deviceScaleFactor: 1, reducedMotion: 'reduce' },
});


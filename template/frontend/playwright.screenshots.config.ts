import { defineConfig } from '@playwright/test';
import base from './playwright.config';

export default defineConfig({
  ...base,
  testIgnore: [],
  testMatch: 'screenshots.spec.ts',
  workers: 1,
  use: { ...base.use, deviceScaleFactor: 1, reducedMotion: 'reduce' },
});


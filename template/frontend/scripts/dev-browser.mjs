import { chromium } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const [destination, mode, theme] = process.argv.slice(2);
const origin = 'http://127.0.0.1:5173';
const errors = [];
const requests = [];
const failed = [];
const safePath = (url) => new URL(url).pathname.slice(0, 500);
const redact = (text) => text
  .replace(/(bearer\s+)[^\s,;]+/gi, '$1[redacted]')
  .replace(/((?:token|password|secret|api[_-]?key)\s*[:=]\s*)[^\s,;]+/gi, '$1[redacted]')
  .slice(0, 1000);

const browser = await chromium.launch();
try {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    reducedMotion: 'reduce',
    serviceWorkers: 'block',
  });
  await context.route('**/*', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.origin === origin && ['GET', 'HEAD'].includes(request.method())) {
      await route.continue();
    } else {
      await route.abort();
    }
  });
  await context.addInitScript((value) => localStorage.setItem('theme', value), theme);
  const page = await context.newPage();
  page.on('pageerror', (error) => { if (errors.length < 50) errors.push(redact(error.message)); });
  page.on('console', (message) => {
    if (message.type() === 'error' && errors.length < 50) errors.push(redact(message.text()));
  });
  page.on('response', (response) => {
    const entry = { method: response.request().method(), path: safePath(response.url()), status: response.status() };
    if (requests.length < 100) requests.push(entry);
    if (response.status() >= 400 && failed.length < 50) failed.push(entry);
  });
  page.on('requestfailed', (request) => {
    if (failed.length < 50) failed.push({ method: request.method(), path: safePath(request.url()), error: request.failure()?.errorText });
  });
  let status = null;
  try {
    const response = await page.goto(origin, { waitUntil: 'domcontentloaded', timeout: 12000 });
    status = response?.status() ?? null;
    await page.getByRole('heading', { name: 'Overview', exact: true }).waitFor({ timeout: 5000 });
  if (destination !== 'Overview') {
    await page.getByRole('button', { name: destination, exact: true }).click();
    await page.getByRole('heading', { name: destination === 'Diagnostics' ? 'System diagnostics' : destination, exact: true }).waitFor({ timeout: 5000 });
  }
  await page.evaluate(() => document.fonts.ready);
  if (destination === 'Overview') {
    await page.getByRole('table').waitFor({ timeout: 5000 });
    await page.getByText('Loading notes…', { exact: true }).waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
  } else if (destination === 'Diagnostics') {
    await page.getByText('Loading metrics…', { exact: true }).waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
  }
  } catch (error) {
    if (mode !== 'diagnostics') throw error;
    errors.push(redact(String(error)));
  }
  const result = { page: destination, status, errors: errors.slice(0, 50),
    requests, failed_requests: failed, viewport: page.viewportSize() };
  if (mode === 'screenshot') {
    result.image = (await page.screenshot({ animations: 'disabled' })).toString('base64');
  } else if (mode === 'accessibility') {
    const audit = await new AxeBuilder({ page }).analyze();
    result.violations = audit.violations.map(({ id, impact, description, helpUrl, nodes }) => ({
      id, impact, description, helpUrl, targets: nodes.map(node => node.target),
    }));
  } else {
    result.aria_snapshot = (await page.locator('body').ariaSnapshot({ timeout: 3000 }).catch(() => '')).slice(0, 20000);
  }
  process.stdout.write(JSON.stringify(result));
} finally {
  await browser.close();
}

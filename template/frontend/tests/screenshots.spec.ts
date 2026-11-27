import { test, expect, type Page } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const output = resolve(process.env.SCREENSHOTS_DIR ?? '../screenshots');
const fixtureNotes = [
  'Review project requirements', 'Prepare API contract', 'Build reusable UI components',
  'Verify deployment configuration', 'Document agent workflow', 'Review accessibility',
  'Test deployment', 'Update documentation', 'Check API responses', 'Review performance',
];

// Showcase data only: no backend, database, or application mutations.
async function showcaseData(page: Page) {
  const createdAt = new Date().toISOString();
  const notes = fixtureNotes.map((text, index) => ({ id: index + 1, text, created_at: createdAt }));
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    switch (path) {
      case '/api/notes':
        await route.fulfill({ json: notes });
        break;
      case '/api/health':
      case '/api/health/ready':
        await route.fulfill({ json: { status: 'ok', dependencies: { sqlite: 'ok' } } });
        break;
      case '/api/diagnostics':
        await route.fulfill({ json: {
          cpu_percent: 18.4, logical_cpus: 8,
          memory_used_bytes: 6 * 1024 ** 3, memory_total_bytes: 16 * 1024 ** 3,
          disk_used_bytes: 114 * 1024 ** 3, disk_total_bytes: 512 * 1024 ** 3,
          process_rss_bytes: 84 * 1024 ** 2, uptime_seconds: 27 * 3600,
        } });
        break;
      case '/api/events':
        await route.fulfill({ contentType: 'text/event-stream', body: 'event: notes-changed\ndata: 1\nretry: 60000\n\n' });
        break;
      default:
        await route.abort();
    }
  });
}

async function capture(page: Page, name: string) {
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: resolve(output, name + '.png'), animations: 'disabled' });
}

async function settings(page: Page) {
  await page.getByRole('button', { name: 'Open settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
  await page.mouse.move(700, 100);
}

test.beforeEach(async ({ page }) => {
  page.on('pageerror', error => console.error('Browser page error:', error));
  page.on('console', message => { if (message.type() === 'error') console.error(message.text()); });
  await mkdir(output, { recursive: true });
  await showcaseData(page);
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible();
  await page.getByRole('button', { name: fixtureNotes[0], exact: true }).click();
  await expect(page.getByRole('button', { name: 'Page 2', exact: true })).toBeInViewport();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
});

test('01-overview-dark', async ({ page }) => {
  await capture(page, '01-overview-dark');
});

test('02-context-menu', async ({ page }) => {
  await page.getByRole('button', { name: 'Prepare API contract', exact: true }).click({ button: 'right' });
  await expect(page.getByRole('menuitem', { name: 'Copy note', exact: true })).toBeVisible();
  await capture(page, '02-context-menu');
});

test('03-command-palette', async ({ page }) => {
  await page.keyboard.press('Control+k');
  await expect(page.getByPlaceholder('Type a command…', { exact: true })).toBeVisible();
  await capture(page, '03-command-palette');
});

test('04-form-validation', async ({ page }) => {
  await page.getByRole('button', { name: 'Add note', exact: true }).click();
  await expect(page.getByText('Enter a note.', { exact: true })).toBeVisible();
  await capture(page, '04-form-validation');
});

test('05-settings', async ({ page }) => {
  await settings(page);
  await capture(page, '05-settings');
});

test('06-toast', async ({ page }) => {
  await settings(page);
  await page.getByRole('button', { name: 'Test notification', exact: true }).click();
  await expect(page.getByText('Notification test', { exact: true })).toBeVisible();
  await capture(page, '06-toast');
});

test('07-diagnostics', async ({ page }) => {
  await page.getByRole('button', { name: 'Diagnostics', exact: true }).click();
  await expect(page.getByText('API process RAM (RSS)', { exact: true })).toBeVisible();
  await capture(page, '07-diagnostics');
});

test('08-schema-form', async ({ page }) => {
  const form = page.getByRole('region', { name: 'Schema-generated note', exact: true });
  test.skip(await form.count() === 0, 'Schema-generated forms are disabled');
  await form.scrollIntoViewIfNeeded();
  const field = form.getByRole('textbox');
  await expect(field).toBeVisible();
  await field.fill('Prepare next release notes');
  await expect(form.getByRole('button', { name: 'Submit', exact: true })).toBeInViewport();
  await expect(form).toBeInViewport();
  await capture(page, '08-schema-form');
});

test('09-settings-toggles', async ({ page }) => {
  await settings(page);
  const motion = page.getByRole('switch', { name: 'Reduce motion', exact: true });
  const success = page.getByRole('switch', { name: 'Success notifications', exact: true });
  // Reduced motion is already enabled by the screenshot browser context.
  await success.click();
  await expect(motion).toHaveAttribute('aria-checked', 'true');
  await expect(success).toHaveAttribute('aria-checked', 'false');
  await capture(page, '09-settings-toggles');
});

test('10-dropdown-menu', async ({ page }) => {
  await page.getByRole('button', { name: 'Workspace actions', exact: true }).click();
  await expect(page.getByRole('menuitem', { name: 'API documentation', exact: true })).toBeVisible();
  await capture(page, '10-dropdown-menu');
});

test('11-sidebar-collapsed', async ({ page }) => {
  await page.getByRole('button', { name: 'Toggle sidebar', exact: true }).click();
  await expect(page.locator('[data-slot="sidebar"][data-state="collapsed"]')).toBeVisible();
  await page.mouse.move(700, 100);
  await capture(page, '11-sidebar-collapsed');
});

test('12-navigation-menu', async ({ page }) => {
  const trigger = page.getByRole('button', { name: 'Resources', exact: true });
  await trigger.click();
  await expect(trigger).toHaveAttribute('aria-expanded', 'true');
  for (const name of ['API documentation', 'OpenAPI schema', 'Service health']) {
    await expect(page.getByRole('link', { name, exact: true })).toBeInViewport();
  }
  await expect(page.getByRole('button', { name: 'Open settings', exact: true })).toBeInViewport();
  await capture(page, '12-navigation-menu');
});

test('13-date-range-popover', async ({ page }) => {
  await page.getByRole('button', { name: 'Filter by creation date', exact: true }).click();
  await page.getByRole('button', { name: 'Last 7 days', exact: true }).click();
  const popover = page.locator('[data-slot="popover-content"]');
  await expect(popover).toBeVisible();
  await expect.poll(async () => {
    const box = await popover.boundingBox();
    const viewport = page.viewportSize();
    return box !== null && viewport !== null && box.y >= 0 && box.y + box.height <= viewport.height && box.x >= 0 && box.x + box.width <= viewport.width;
  }).toBe(true);
  await capture(page, '13-date-range-popover');
});

for (const [label, id] of [['Light', 'light'], ['OLED', 'oled'], ['Solarized Light (Warm)', 'solarized-light'], ['Solarized Dark', 'solarized-dark']]) {
  test('theme-' + id, async ({ page }) => {
    await settings(page);
    await page.getByRole('combobox', { name: 'Color theme', exact: true }).click();
    await page.getByRole('option', { name: label, exact: true }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', id);
    await page.getByRole('button', { name: 'Overview', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible();
    await capture(page, 'theme-' + id);
  });
}

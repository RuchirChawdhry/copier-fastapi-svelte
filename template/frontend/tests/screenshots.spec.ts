import { test, expect, type Page } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const output = resolve(process.env.SCREENSHOTS_DIR ?? '../screenshots');
async function capture(page: Page, name: string) {
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: resolve(output, name + '.png'), animations: 'disabled' });
}

test('capture application screens', async ({ page, request }) => {
  page.on('pageerror', error => console.error('Browser page error:', error));
  page.on('console', message => { if (message.type() === 'error') console.error(message.text()); });
  await mkdir(output, { recursive: true });
  for (const note of await (await request.get('/api/notes')).json()) {
    await request.delete('/api/notes/' + note.id);
  }
  for (const text of ['Review project requirements', 'Prepare API contract', 'Build reusable UI components', 'Verify deployment configuration', 'Document agent workflow', 'Review accessibility', 'Test deployment', 'Update documentation', 'Check API responses', 'Review performance']) {
    expect((await request.post('/api/notes', { data: { text } })).ok()).toBeTruthy();
  }
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible({ timeout: 20000 });
  await expect(page.getByRole('button', { name: 'Review project requirements', exact: true })).toBeVisible({ timeout: 20000 });
  await page.getByRole('button', { name: 'Review project requirements', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Page 2', exact: true })).toBeInViewport();
  await capture(page, '01-overview-dark');
  await page.getByRole('button', { name: 'Resources', exact: true }).click();
  await expect(page.getByRole('link', { name: /OpenAPI schema/ })).toBeVisible();
  await capture(page, '12-navigation-menu');
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Filter by creation date' }).click();
  await page.getByRole('button', { name: 'Last 7 days' }).click();
  const popover = page.locator('[data-slot="popover-content"]');
  await expect(popover).toBeVisible();
  await expect.poll(async () => {
    const box = await popover.boundingBox();
    return box !== null && box.y >= 0 && box.y + box.height <= 800 && box.x >= 0 && box.x + box.width <= 1280;
  }).toBe(true);
  await capture(page, '13-date-range-popover');
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Workspace actions' }).click();
  await expect(page.getByRole('menuitem', { name: 'API documentation' })).toBeVisible();
  await capture(page, '10-dropdown-menu');
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Toggle sidebar', exact: true }).click();
  await expect(page.locator('[data-slot="sidebar"][data-state="collapsed"]')).toBeVisible();
  await page.mouse.move(700, 100);
  await capture(page, '11-sidebar-collapsed');
  await page.getByRole('button', { name: 'Toggle sidebar', exact: true }).click();
  await expect(page.locator('[data-slot="sidebar"][data-state="expanded"]')).toBeVisible();
  const schemaForm = page.getByRole('heading', { name: 'Schema-generated note' });
  if (await schemaForm.count()) {
    await schemaForm.scrollIntoViewIfNeeded();
    await capture(page, '08-schema-form');
    await page.evaluate(() => window.scrollTo(0, 0));
  }
  await page.getByText('Prepare API contract').click({ button: 'right' });
  await expect(page.getByRole('menuitem', { name: 'Copy note' })).toBeVisible();
  await capture(page, '02-context-menu');
  await page.keyboard.press('Escape');
  await page.keyboard.press('Control+k');
  await expect(page.getByPlaceholder('Type a command…')).toBeVisible();
  await capture(page, '03-command-palette');
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Add note' }).click();
  await expect(page.getByText('Enter a note.')).toBeVisible();
  await capture(page, '04-form-validation');
  await page.getByRole('button', { name: 'Settings' }).click();
  await capture(page, '05-settings');
  await page.getByRole('switch', { name: 'Reduce motion' }).click();
  await page.getByRole('switch', { name: 'Success notifications' }).click();
  await capture(page, '09-settings-toggles');
  await page.getByRole('switch', { name: 'Success notifications' }).click();
  for (const [label, id] of [['Light', 'light'], ['OLED', 'oled'], ['Solarized Light (Warm)', 'solarized-light'], ['Solarized Dark', 'solarized-dark']]) {
    await page.getByRole('combobox', { name: 'Color theme' }).click();
    await page.getByRole('option', { name: label, exact: true }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', id);
    await page.getByRole('button', { name: 'Overview' }).click();
    await capture(page, 'theme-' + id);
    await page.getByRole('button', { name: 'Settings' }).click();
  }
  await page.getByRole('combobox', { name: 'Color theme' }).click();
  await page.getByRole('option', { name: 'Dark', exact: true }).click();
  await page.getByRole('button', { name: 'Test notification' }).click();
  await expect(page.getByText('Notification test', { exact: true })).toBeVisible();
  await capture(page, '06-toast');
  await page.getByRole('button', { name: 'Diagnostics' }).click();
  await expect(page.getByText('API process RAM (RSS)')).toBeVisible();
  await capture(page, '07-diagnostics');
});


import { test, expect } from '@playwright/test';

test('notes, context menu, command palette and five persisted themes', async ({ page }) => {
  page.on('pageerror', (error) => console.error('Browser page error:', error));
  page.on('console', (message) => { if (message.type() === 'error') console.error(message.text()); });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
  await page.getByRole('button', { name: 'Add note' }).click();
  await expect(page.getByText('Enter a note.')).toBeVisible();
  const note = 'Browser integration ' + Date.now();
  await page.getByRole('textbox', { name: 'New note' }).fill(note);
  await page.getByRole('button', { name: 'Add note' }).click();
  await expect(page.getByText(note, { exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Filter notes' }).fill('no matching value');
  await expect(page.getByText('No notes found.')).toBeVisible();
  await page.getByRole('textbox', { name: 'Filter notes' }).clear();
  await page.getByRole('button', { name: note, exact: true }).click({ button: 'right' });
  await expect(page.getByRole('menuitem', { name: 'Delete note' })).toBeVisible();
  await expect(page.getByRole('menuitem', { name: 'Delete note' }).locator('svg')).toHaveCount(1);
  await page.keyboard.press('Escape');
  await page.keyboard.press('Control+k');
  await expect(page.getByPlaceholder('Type a command…')).toBeVisible();
  await expect(page.getByText('Open settings', { exact: true }).locator('[data-menu-icon]')).toHaveCount(1);
  await page.getByText('Open settings', { exact: true }).click();
  await page.getByRole('switch', { name: 'Reduce motion' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-reduced-motion', '');
  await page.getByRole('switch', { name: 'Success notifications' }).click();
  await expect(page.getByRole('switch', { name: 'Success notifications' })).toHaveAttribute('aria-checked', 'false');
  for (const [label, id] of [
    ['Dark', 'dark'], ['Light', 'light'], ['OLED', 'oled'],
    ['Solarized Light (Warm)', 'solarized-light'], ['Solarized Dark', 'solarized-dark'],
  ]) {
    await page.getByRole('combobox', { name: 'Color theme' }).click();
    await page.getByRole('option', { name: label, exact: true }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', id);
  }
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-reduced-motion', '');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'Success notifications' })).toHaveAttribute('aria-checked', 'false');
  await page.getByRole('switch', { name: 'Success notifications' }).click();
  await page.getByRole('button', { name: 'Overview', exact: true }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'solarized-dark');
  await page.getByRole('button', { name: note, exact: true }).click({ button: 'right' });
  await page.getByRole('menuitem', { name: 'Delete note' }).click();
  await expect(page.getByRole('button', { name: note, exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Diagnostics' }).click();
  await expect(page.getByText('API process RAM (RSS)')).toBeVisible();
});


test('diagnostics cache is reused on immediate navigation', async ({ page }) => {
  let requests = 0;
  page.on('request', (request) => {
    if (new URL(request.url()).pathname === '/api/diagnostics') requests++;
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Diagnostics' }).click();
  await expect(page.getByText('API process RAM (RSS)')).toBeVisible();
  await page.getByRole('button', { name: 'Overview', exact: true }).click();
  await page.getByRole('button', { name: 'Diagnostics' }).click();
  await expect(page.getByText('API process RAM (RSS)')).toBeVisible();
  expect(requests).toBe(1);
  await page.getByRole('button', { name: 'Refresh metrics' }).click();
  await expect.poll(() => requests).toBe(2);
});


test('workspace menu and sidebar keyboard navigation', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Workspace actions' }).click();
  await expect(page.getByRole('menuitem', { name: 'API documentation' })).toBeVisible();
  await page.getByRole('menuitem', { name: 'Open settings' }).click();
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  await page.keyboard.press('Control+b');
  await expect(page.locator('[data-slot="sidebar"][data-state="collapsed"]')).toBeVisible();
  await page.getByRole('button', { name: 'Overview', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
  await page.reload();
  await expect(page.locator('[data-slot="sidebar"][data-state="collapsed"]')).toBeVisible();
  await page.getByRole('button', { name: 'Toggle sidebar', exact: true }).click();
  await expect(page.locator('[data-slot="sidebar"][data-state="expanded"]')).toBeVisible();
});

test('mobile sidebar opens and closes on navigation', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Toggle sidebar', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

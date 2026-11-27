import { test, expect } from '@playwright/test';

test('notes, context menu, command palette and five persisted themes', async ({ page }) => {
  page.on('pageerror', (error) => console.error('Browser page error:', error));
  page.on('console', (message) => { if (message.type() === 'error') console.error(message.text()); });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
  const note = 'Browser integration ' + Date.now();
  await page.getByRole('textbox', { name: 'New note' }).fill(note);
  await page.getByRole('button', { name: 'Add note' }).click();
  await expect(page.getByText(note, { exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Filter notes' }).fill('no matching value');
  await expect(page.getByText('No notes found.')).toBeVisible();
  await page.getByRole('textbox', { name: 'Filter notes' }).clear();
  await page.getByRole('button', { name: note, exact: true }).click({ button: 'right' });
  await expect(page.getByRole('menuitem', { name: 'Delete note' })).toBeVisible();
  await page.keyboard.press('Escape');
  await page.keyboard.press('Control+k');
  await expect(page.getByPlaceholder('Type a command…')).toBeVisible();
  await page.getByText('Open settings', { exact: true }).click();
  for (const [label, id] of [
    ['Dark', 'dark'], ['Light', 'light'], ['OLED', 'oled'],
    ['Solarized Light (Warm)', 'solarized-light'], ['Solarized Dark', 'solarized-dark'],
  ]) {
    await page.getByRole('button', { name: label, exact: true }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', id);
  }
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'solarized-dark');
  await page.getByRole('button', { name: note, exact: true }).click({ button: 'right' });
  await page.getByRole('menuitem', { name: 'Delete note' }).click();
  await expect(page.getByRole('button', { name: note, exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Diagnostics' }).click();
  await expect(page.getByText('API process RAM (RSS)')).toBeVisible();
});


import { test, expect } from '@playwright/test';

test('notes, context menu, command palette and five persisted themes', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible();
  const note = 'Browser integration ' + Date.now();
  await page.getByRole('textbox', { name: 'New note' }).fill(note);
  await page.getByRole('button', { name: 'Add note' }).click();
  await expect(page.getByText(note)).toBeVisible();
  await page.getByText(note).click({ button: 'right' });
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
  await page.getByText(note).click({ button: 'right' });
  await page.getByRole('menuitem', { name: 'Delete note' }).click();
  await expect(page.getByText(note)).toHaveCount(0);
});


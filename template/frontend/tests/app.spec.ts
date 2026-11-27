import { test, expect } from '@playwright/test';

test('notes, context menu, command palette and five persisted themes', async ({ page }) => {
  page.on('pageerror', (error) => console.error('Browser page error:', error));
  page.on('console', (message) => { if (message.type() === 'error') console.error(message.text()); });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Add note', exact: true }).click();
  await expect(page.getByText('Enter a note.', { exact: true })).toBeVisible();
  const note = 'Browser integration ' + Date.now();
  await page.getByRole('textbox', { name: 'New note', exact: true }).fill(note);
  await page.getByRole('button', { name: 'Add note', exact: true }).click();
  await expect(page.getByText(note, { exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Filter notes', exact: true }).fill('no matching value');
  await expect(page.getByText('No notes found.', { exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Filter notes', exact: true }).clear();
  await page.getByRole('button', { name: note, exact: true }).click({ button: 'right' });
  await expect(page.getByRole('menuitem', { name: 'Delete note', exact: true })).toBeVisible();
  await expect(page.getByRole('menuitem', { name: 'Delete note', exact: true }).locator('svg')).toHaveCount(1);
  await page.keyboard.press('Escape');
  await page.keyboard.press('Control+k');
  await expect(page.getByPlaceholder('Type a command…', { exact: true })).toBeVisible();
  await expect(page.getByText('Open settings', { exact: true }).locator('[data-menu-icon]')).toHaveCount(1);
  await page.getByText('Open settings', { exact: true }).click();
  await page.getByRole('switch', { name: 'Reduce motion', exact: true }).click();
  await expect(page.locator('html')).toHaveAttribute('data-reduced-motion', '');
  await page.getByRole('switch', { name: 'Success notifications', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'Success notifications', exact: true })).toHaveAttribute('aria-checked', 'false');
  for (const [label, id] of [
    ['Dark', 'dark'], ['Light', 'light'], ['OLED', 'oled'],
    ['Solarized Light (Warm)', 'solarized-light'], ['Solarized Dark', 'solarized-dark'],
  ]) {
    await page.getByRole('combobox', { name: 'Color theme', exact: true }).click();
    await page.getByRole('option', { name: label, exact: true }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', id);
  }
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-reduced-motion', '');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('switch', { name: 'Success notifications', exact: true })).toHaveAttribute('aria-checked', 'false');
  await page.getByRole('switch', { name: 'Success notifications', exact: true }).click();
  await page.getByRole('button', { name: 'Overview', exact: true }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'solarized-dark');
  await page.getByRole('button', { name: note, exact: true }).click({ button: 'right' });
  await page.getByRole('menuitem', { name: 'Delete note', exact: true }).click();
  await expect(page.getByRole('button', { name: note, exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Diagnostics', exact: true }).click();
  await expect(page.getByText('API process RAM (RSS)', { exact: true })).toBeVisible();
});


test('diagnostics cache is reused on immediate navigation', async ({ page }) => {
  let requests = 0;
  page.on('request', (request) => {
    if (new URL(request.url()).pathname === '/api/diagnostics') requests++;
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Diagnostics', exact: true }).click();
  await expect(page.getByText('API process RAM (RSS)', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Overview', exact: true }).click();
  await page.getByRole('button', { name: 'Diagnostics', exact: true }).click();
  await expect(page.getByText('API process RAM (RSS)', { exact: true })).toBeVisible();
  expect(requests).toBe(1);
  await page.getByRole('button', { name: 'Refresh metrics', exact: true }).click();
  await expect.poll(() => requests).toBe(2);
});


test('header settings gear opens settings', async ({ page }) => {
  await page.goto('/');
  const search = page.getByRole('button', { name: 'Search commands', exact: true });
  const gear = page.getByRole('button', { name: 'Open settings', exact: true });
  await expect(search).toBeVisible();
  await expect(gear).toBeVisible();
  const searchBox = await search.boundingBox();
  const gearBox = await gear.boundingBox();
  expect(gearBox!.x).toBeGreaterThanOrEqual(searchBox!.x + searchBox!.width);
  await gear.click();
  await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
  await expect(gear).toHaveAttribute('aria-current', 'page');
});

test('workspace menu and sidebar keyboard navigation', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Workspace actions', exact: true }).click();
  await expect(page.getByRole('menuitem', { name: 'API documentation', exact: true })).toBeVisible();
  await page.getByRole('menuitem', { name: 'Open settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
  await page.keyboard.press('Control+b');
  await expect(page.locator('[data-slot="sidebar"][data-state="collapsed"]')).toBeVisible();
  await page.getByRole('button', { name: 'Overview', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible();
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
  await page.getByRole('dialog').getByRole('button', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
  await expect(page.getByRole('dialog')).toHaveCount(0);
});


test('resource navigation, pagination and UTC date filtering', async ({ page, request }) => {
  const notes = [];
  for (let i = 0; i < 9; i++) {
    const response = await request.post('/api/notes', { data: { text: 'Pagination fixture ' + i } });
    expect(response.ok()).toBeTruthy();
    notes.push(await response.json() as { id: number });
  }
  try {
    await page.goto('/');
    await page.getByRole('button', { name: 'Resources', exact: true }).click();
    await expect(page.getByRole('link', { name: 'OpenAPI schema', exact: true })).toHaveAttribute('href', '/openapi.json');
    const contract = await request.get('/openapi.json');
    expect(contract.ok()).toBeTruthy();
    expect((await contract.json()).paths['/api/notes']).toBeDefined();
    expect(await (await request.get('/docs')).text()).toContain('Swagger UI');
    await page.keyboard.press('Escape');
    await page.getByRole('button', { name: 'Page 2', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Pagination fixture 8', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Filter by creation date', exact: true }).click();
    await page.getByRole('button', { name: 'Previous month', exact: true }).click();
    await page.getByRole('button', { name: 'Apply range', exact: true }).click();
    await expect(page.getByText('No notes found.', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Filter by creation date', exact: true }).click();
    await page.getByRole('button', { name: 'Last 7 days', exact: true }).click();
    await page.getByRole('button', { name: 'Apply range', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Pagination fixture 0', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Page 1', exact: true })).toHaveAttribute('aria-current', 'page');
    await page.getByRole('button', { name: 'Filter by creation date', exact: true }).click();
    await page.getByRole('button', { name: 'Clear filter', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Filter by creation date', exact: true })).toContainText('Any date');
    const viewport = page.locator('[aria-label="Notes table scroll area"] [data-slot="scroll-area-viewport"]');
    await expect.poll(() => viewport.evaluate(el => el.scrollHeight > el.clientHeight)).toBe(true);
  } finally {
    for (const note of notes) await request.delete('/api/notes/' + note.id);
  }
});


test('note API validation errors identify the operation and field', async ({ page }) => {
  await page.goto('/');
  await page.route('**/api/notes', async (route) => {
    if (route.request().method() !== 'POST') return route.continue();
    await route.fulfill({ status: 422, json: { detail: [{ loc: ['body', 'text'], msg: 'Rejected by server' }] } });
  });
  await page.getByRole('textbox', { name: 'New note', exact: true }).fill('Valid client input');
  await page.getByRole('button', { name: 'Add note', exact: true }).click();
  await expect(page.getByText(/Could not save note: text: Rejected by server/)).toBeVisible();
});


test('development browser probe returns live accessibility and screenshot evidence', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto('/');
  const { execFile } = await import('node:child_process');
  const { promisify } = await import('node:util');
  const execute = promisify(execFile);
  const diagnostic = await execute(process.execPath, ['scripts/dev-browser.mjs', 'Overview', 'diagnostics', 'dark'], { timeout: 45000 });
  const report = JSON.parse(diagnostic.stdout);
  expect(report.aria_snapshot).toContain('Overview');
  expect(report.status).toBe(200);
  const screenshot = await execute(process.execPath, ['scripts/dev-browser.mjs', 'Settings', 'screenshot', 'dark'], { timeout: 45000, maxBuffer: 8 * 1024 * 1024 });
  expect(Buffer.from(JSON.parse(screenshot.stdout).image, 'base64').subarray(0, 8).toString('hex')).toBe('89504e470d0a1a0a');
  const audit = await execute(process.execPath, ['scripts/dev-browser.mjs', 'Settings', 'accessibility', 'dark'], { timeout: 45000 });
  expect(Array.isArray(JSON.parse(audit.stdout).violations)).toBe(true);
});

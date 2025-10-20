const { test, expect } = require('@playwright/test');

test('Google homepage loads', async ({ page }) => {
  await page.goto('https://www.google.com');
  await expect(page).toHaveTitle(/Google/);
});

test('Google search box is visible', async ({ page }) => {
  await page.goto('https://www.google.com');
  const searchBox = page.locator('textarea[name="q"]');
  await expect(searchBox).toBeVisible();
});

test('Google search works', async ({ page }) => {
  await page.goto('https://www.google.com');
  await page.fill('textarea[name="q"]', 'Playwright');
  await page.press('textarea[name="q"]', 'Enter');
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveURL(/search/);
});

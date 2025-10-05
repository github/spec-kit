import { test, expect } from '@playwright/test'

test.describe('Smoke Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('http://localhost:5173')
    await expect(page).toHaveTitle(/PrintMarket/)
  })
  
  test('login page is accessible', async ({ page }) => {
    await page.goto('http://localhost:5173/login')
    await expect(page.locator('h1')).toContainText('PrintMarket')
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
  })
  
  test('register page is accessible', async ({ page }) => {
    await page.goto('http://localhost:5173/register')
    await expect(page.locator('h1')).toContainText('Join PrintMarket')
  })
  
  test('navigation works', async ({ page }) => {
    await page.goto('http://localhost:5173/login')
    await page.click('text=Register here')
    await expect(page).toHaveURL(/.*register/)
  })
})

import { test, expect } from '@playwright/test'

test('homepage redirects to login', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/.*login/)
})

test('login page loads', async ({ page }) => {
  await page.goto('/login')
  await expect(page.locator('h1')).toContainText('PrintMarket')
  await expect(page.locator('input[type="email"]')).toBeVisible()
})

test('register page loads', async ({ page }) => {
  await page.goto('/register')
  await expect(page.locator('h1')).toContainText('Join PrintMarket')
})

test('can navigate between login and register', async ({ page }) => {
  await page.goto('/login')
  await page.click('text=Register here')
  await expect(page).toHaveURL(/.*register/)
  
  await page.click('text=Login here')
  await expect(page).toHaveURL(/.*login/)
})

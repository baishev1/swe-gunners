import { expect, test } from '@playwright/test'

import { PASSWORD, signIn } from './support.ts'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('language', 'en'))
})

test('an expired access token is refreshed without signing the user out', async ({ page }) => {
  await signIn(page, 'attendee@biletflow.dev', PASSWORD)
  await page.evaluate(() => localStorage.setItem('access_token', 'expired'))

  const refreshed = page.waitForResponse(
    (response) => response.url().endsWith('/auth/refresh') && response.ok(),
  )
  await page.reload()
  await refreshed

  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
  expect(await page.evaluate(() => localStorage.getItem('access_token'))).not.toBe('expired')
})

test('a rejected refresh token sends the user to the login page', async ({ page }) => {
  await signIn(page, 'attendee@biletflow.dev', PASSWORD)
  await page.evaluate(() => {
    localStorage.setItem('access_token', 'expired')
    localStorage.setItem('refresh_token', 'expired')
  })

  await page.reload()

  await expect(page).toHaveURL(/\/login$/)
  expect(await page.evaluate(() => localStorage.getItem('refresh_token'))).toBeNull()
})

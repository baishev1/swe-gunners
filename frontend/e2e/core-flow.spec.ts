import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

const PASSWORD = 'password123'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('language', 'en'))
})

async function signIn(page: Page, email: string, password: string) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
}

function createVerifyToken(userId: string) {
  const script =
    'import sys; from types import SimpleNamespace; ' +
    'from features.auth.service import auth_service; ' +
    'print(auth_service.create_verify_token(SimpleNamespace(id=sys.argv[1])))'
  return execFileSync('uv', ['run', 'python', '-c', script, userId], {
    cwd: path.resolve(import.meta.dirname, '../../backend'),
    encoding: 'utf-8',
  }).trim()
}

test('organizer publishes an event and an anonymous visitor finds it', async ({ page }) => {
  const stamp = Date.now()
  const title = `E2E Concert ${stamp}`
  const venueName = `E2E Hall ${stamp}`

  await signIn(page, 'organizer@biletflow.dev', PASSWORD)

  await page.goto('/organizer/events/new')
  await page.getByLabel('Venue name').fill(venueName)
  await page.getByLabel('Address').fill('1 Test Street')
  await page.getByRole('button', { name: 'Add venue' }).click()
  await expect(page.getByLabel('Venue name')).toHaveValue('')

  await page.getByLabel('Title').fill(title)
  await page.getByLabel('Category').fill('Music')
  await page
    .getByLabel('Venue', { exact: true })
    .selectOption({ label: `${venueName}, 1 Test Street` })
  await page.getByLabel('Starts').fill('2031-05-01T19:00')
  await page.getByLabel('Ends').fill('2031-05-01T22:00')
  await page.getByLabel('Capacity').fill('100')
  await page.getByRole('button', { name: 'Create event' }).click()

  await expect(page.getByRole('heading', { name: title })).toBeVisible()

  await page.getByLabel('Name').fill('General')
  await page.getByLabel('Quantity').fill('50')
  await page.getByRole('button', { name: 'Add ticket type' }).click()
  await expect(page.getByText('General · ')).toBeVisible()

  await page.getByRole('button', { name: 'Publish', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Unpublish' })).toBeVisible()

  await page.goto('/')
  await page.getByRole('button', { name: 'Sign out' }).click()

  await page.goto('/events')
  await page.getByRole('link', { name: new RegExp(title) }).click()
  await expect(page.getByRole('heading', { name: title })).toBeVisible()
  await expect(page.getByText('General')).toBeVisible()
})

test('attendee registers, verifies the email and signs in', async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`

  await page.goto('/register')
  await page.getByLabel('Full name').fill('E2E Attendee')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(PASSWORD)
  const registered = page.waitForResponse(
    (response) => response.url().endsWith('/auth/register') && response.ok(),
  )
  await page.getByRole('button', { name: 'Create account' }).click()
  const { id } = (await (await registered).json()) as { id: string }
  await expect(page.getByText(`We sent a verification link to ${email}.`)).toBeVisible()

  await page.goto(`/verify-email?token=${createVerifyToken(id)}`)
  await expect(page.getByText('Email verified')).toBeVisible()

  await signIn(page, email, PASSWORD)
  await expect(page.getByText('Event ticketing platform')).toBeVisible()
})

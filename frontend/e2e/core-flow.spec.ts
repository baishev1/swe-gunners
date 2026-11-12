import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { expect, test } from '@playwright/test'
import type { APIRequestContext, Page } from '@playwright/test'

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

async function apiToken(request: APIRequestContext, email: string) {
  const response = await request.post('/api/v1/auth/login', {
    data: { email, password: PASSWORD },
  })
  expect(response.ok()).toBeTruthy()
  const { access_token } = (await response.json()) as { access_token: string }
  return { Authorization: `Bearer ${access_token}` }
}

async function api(
  request: APIRequestContext,
  method: 'get' | 'post' | 'patch',
  url: string,
  headers: Record<string, string>,
  data?: unknown,
) {
  const response = await request[method](`/api/v1${url}`, { headers, data })
  expect(response.ok(), `${method.toUpperCase()} ${url}: ${await response.text()}`).toBeTruthy()
  return response.json()
}

test('attendee buys a paid ticket, asks support and gets in once', async ({ page, request }) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  const eventAdmin = await apiToken(request, 'eventadmin@biletflow.dev')
  const admin = await apiToken(request, 'admin@biletflow.dev')
  const attendee = await apiToken(request, 'attendee@biletflow.dev')
  const start = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)

  const venue = await api(request, 'post', '/venues', organizer, {
    name: `Core Flow Hall ${Date.now()}`,
    address: '1 Abay Ave',
  })
  const event = await api(request, 'post', '/events', organizer, {
    title: `Core Flow ${Date.now()}`,
    category: 'Music',
    venue_id: venue.id,
    start_time: start.toISOString(),
    end_time: new Date(start.getTime() + 2 * 60 * 60 * 1000).toISOString(),
    capacity: 20,
  })
  const ticketType = await api(request, 'post', `/ticket-types?event_id=${event.id}`, organizer, {
    name: 'Standard',
    price: 5000,
    quantity: 20,
  })
  await api(request, 'post', `/events/publish?event_id=${event.id}`, organizer)

  await api(request, 'patch', '/organizers/profile', organizer, {
    payout_recipient_name: 'Demo Events LLP',
    payout_iban: 'KZ86125KZT5004100100',
    payout_bin: '123456789012',
  })
  await api(request, 'post', '/organizers/verify-identity', organizer)
  await api(request, 'post', `/paid-sales/pay-fee?event_id=${event.id}`, organizer, {
    simulate_failure: false,
  })
  await api(request, 'post', `/paid-sales/accept-terms?event_id=${event.id}`, organizer)
  await api(request, 'post', `/paid-sales/activate?event_id=${event.id}`, organizer)

  const campaign = await api(request, 'post', `/promo/campaigns?event_id=${event.id}`, organizer, {
    name: 'Launch',
    discount_type: 'percent',
    discount_value: 20,
    start_time: new Date().toISOString(),
    end_time: start.toISOString(),
    max_redemptions: 10,
    ticket_type_ids: [ticketType.id],
  })
  const staffUser = await api(request, 'get', '/auth/me', eventAdmin)
  await api(request, 'post', `/checkin/staff?event_id=${event.id}`, organizer, {
    user_id: staffUser.id,
    can_undo_check_in: true,
    can_manage_support: false,
  })

  await signIn(page, 'attendee@biletflow.dev', PASSWORD)
  await page.goto(`/events/detail?event_id=${event.id}`)
  await page.getByRole('link', { name: 'Get tickets' }).click()
  await expect(page.getByText('Standard')).toBeVisible()
  await page.getByPlaceholder('e.g. Arman Bekov').fill('Demo Attendee')
  await page.getByPlaceholder('e.g. arman@example.kz').fill('attendee@biletflow.dev')
  await page.getByRole('button', { name: 'Pay 5000 ₸ (Simulate)' }).click()

  await page.waitForURL(/\/tickets\?order_id=/)
  await expect(page.getByText('VALID', { exact: true })).toBeVisible()
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download Printable PDF' }).click()
  expect((await download).suggestedFilename()).toMatch(/^ticket-.+\.pdf$/)

  const orderId = new URL(page.url()).searchParams.get('order_id')
  const [ticket] = await api(request, 'get', `/tickets?order_id=${orderId}`, attendee)

  const supportCase = await api(request, 'post', '/support/cases', attendee, {
    target: 'organizer',
    event_id: event.id,
    category: 'ticket_delivery',
    subject: 'Ticket question',
    message: 'Is my ticket valid?',
  })
  await api(request, 'post', `/support/messages?case_id=${supportCase.id}`, organizer, {
    body: 'Yes, see you there.',
  })
  const messages = await api(
    request,
    'get',
    `/support/messages?case_id=${supportCase.id}`,
    attendee,
  )
  expect(messages.map((m: { body: string }) => m.body)).toContain('Yes, see you there.')

  const verify = (qrToken: string) =>
    api(request, 'get', `/tickets/verify?event_id=${event.id}&qr_token=${qrToken}`, eventAdmin)
  expect((await verify(ticket.qr_token)).valid).toBe(true)
  expect((await verify(campaign.code)).valid).toBe(false)

  const checkIn = `/api/v1/tickets/check-in?event_id=${event.id}&ticket_id=${ticket.id}`
  expect((await request.post(checkIn, { headers: eventAdmin })).status()).toBe(200)
  expect((await request.post(checkIn, { headers: eventAdmin })).status()).toBe(400)

  await api(request, 'post', `/admin/events/suspend?event_id=${event.id}`, admin)
  const blocked = await request.post('/api/v1/orders', {
    headers: attendee,
    data: {
      event_id: event.id,
      customer_name: 'Demo Attendee',
      customer_email: 'attendee@biletflow.dev',
      items: [{ ticket_type_id: ticketType.id, quantity: 1 }],
    },
  })
  expect(blocked.status()).toBe(400)
})

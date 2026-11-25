import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { expect } from '@playwright/test'
import type { APIRequestContext, Page } from '@playwright/test'

export const PASSWORD = 'password123'

export function createVerifyToken(userId: string) {
  const script =
    'import sys; from types import SimpleNamespace; ' +
    'from features.auth.service import auth_service; ' +
    'print(auth_service.create_verify_token(SimpleNamespace(id=sys.argv[1])))'
  return execFileSync('uv', ['run', 'python', '-c', script, userId], {
    cwd: path.resolve(import.meta.dirname, '../../backend'),
    encoding: 'utf-8',
  }).trim()
}

export async function signIn(page: Page, email: string, password: string) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
}

export async function apiToken(request: APIRequestContext, email: string) {
  const response = await request.post('/api/v1/auth/login', {
    data: { email, password: PASSWORD },
  })
  expect(response.ok()).toBeTruthy()
  const { access_token } = (await response.json()) as { access_token: string }
  return { Authorization: `Bearer ${access_token}` }
}

export async function api(
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

/** Creates and publishes an event with one ticket type through the API. */
export async function publishedEvent(
  request: APIRequestContext,
  organizer: Record<string, string>,
  { title, price, quantity = 20 }: { title: string; price: number; quantity?: number },
) {
  const start = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  const venue = await api(request, 'post', '/venues', organizer, {
    name: `${title} Hall`,
    address: '1 Abay Ave',
  })
  const event = await api(request, 'post', '/events', organizer, {
    title,
    category: 'Music',
    venue_id: venue.id,
    start_time: start.toISOString(),
    end_time: new Date(start.getTime() + 2 * 60 * 60 * 1000).toISOString(),
    capacity: quantity,
  })
  const ticketType = await api(request, 'post', `/ticket-types?event_id=${event.id}`, organizer, {
    name: 'Standard',
    price,
    quantity,
  })
  await api(request, 'post', `/events/publish?event_id=${event.id}`, organizer)
  return { event, ticketType, start }
}

/** Runs the simulated Paid Sales Activation checklist (SRS 3.2) for one event. */
export async function activatePaidSales(
  request: APIRequestContext,
  organizer: Record<string, string>,
  eventId: string,
) {
  await api(request, 'patch', '/organizers/profile', organizer, {
    payout_recipient_name: 'Demo Events LLP',
    payout_iban: 'KZ86125KZT5004100100',
    payout_bin: '123456789012',
  })
  await api(request, 'post', '/organizers/verify-identity', organizer)
  await api(request, 'post', `/paid-sales/pay-fee?event_id=${eventId}`, organizer, {
    simulate_failure: false,
  })
  await api(request, 'post', `/paid-sales/accept-terms?event_id=${eventId}`, organizer)
  await api(request, 'post', `/paid-sales/activate?event_id=${eventId}`, organizer)
}

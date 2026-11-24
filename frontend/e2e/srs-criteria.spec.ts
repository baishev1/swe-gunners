import { expect, test } from '@playwright/test'

import { PASSWORD, activatePaidSales, api, apiToken, publishedEvent, signIn } from './support.ts'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('language', 'en'))
})

// SRS §11 #1: an organizer can publish a free event and distribute valid tickets.
test('attendee registers for a free event and gets a valid ticket', async ({ page, request }) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  const { event } = await publishedEvent(request, organizer, {
    title: `Free Lecture ${Date.now()}`,
    price: 0,
  })

  await signIn(page, 'attendee@biletflow.dev', PASSWORD)
  await page.goto(`/events/detail?event_id=${event.id}`)
  await expect(page.getByText('Free', { exact: true })).toBeVisible()
  // No policy was set, so the platform default is shown (SRS 4.9).
  const defaultPolicy = /The organizer has not set a refund policy/
  await expect(page.getByText(defaultPolicy)).toBeVisible()
  await page.getByRole('link', { name: 'Get tickets' }).click()
  await expect(page.getByText(defaultPolicy)).toBeVisible()

  await page.getByLabel('Full name').fill('Free Attendee')
  await page.getByLabel('Email address').fill('attendee@biletflow.dev')
  // Free registration needs no payment step (SRS 4.4).
  await expect(page.getByText('Demonstration payment simulation')).toBeHidden()
  await page.getByRole('button', { name: 'Complete free registration' }).click()

  await page.waitForURL(/\/tickets\?order_id=/)
  await expect(page.getByText('Valid', { exact: true })).toBeVisible()

  const orderId = new URL(page.url()).searchParams.get('order_id')
  const attendee = await apiToken(request, 'attendee@biletflow.dev')
  const order = await api(request, 'get', `/orders/detail?order_id=${orderId}`, attendee)
  expect(order.total_amount_kzt).toBe(0)
  expect(order.status).toBe('paid')

  // The organizer sees the registration in the attendee list.
  const attendees = await api(
    request,
    'get',
    `/tickets/event-attendees?event_id=${event.id}`,
    organizer,
  )
  expect(attendees.map((a: { attendee_name: string }) => a.attendee_name)).toContain(
    'Free Attendee',
  )
})

// SRS §11 #7: an attendee scans a Campaign QR Code, gets a valid discount and
// completes an order attributed to the campaign.
test('attendee buys through a campaign link with the discount applied', async ({
  page,
  request,
}) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  // 5000 KZT, stored in tiyn.
  const { event, ticketType, start } = await publishedEvent(request, organizer, {
    title: `Campaign Concert ${Date.now()}`,
    price: 500000,
  })
  await activatePaidSales(request, organizer, event.id)
  const campaign = await api(request, 'post', `/promo/campaigns?event_id=${event.id}`, organizer, {
    name: 'Instagram',
    discount_type: 'percent',
    discount_value: 20,
    end_time: start.toISOString(),
    max_redemptions: 10,
    ticket_type_ids: [ticketType.id],
  })

  await signIn(page, 'attendee@biletflow.dev', PASSWORD)
  // Open the link the Campaign QR Code encodes, as a phone camera would.
  const link = new URL(campaign.link)
  await page.goto(`${link.pathname}${link.search}`)
  await expect(page.getByRole('status').filter({ hasText: campaign.code })).toContainText('−20%')
  await page.getByRole('link', { name: 'Get tickets' }).click()

  // The attendee sees the code, the discount and the new total before paying.
  await expect(page.getByText(`Promo code ${campaign.code}`)).toBeVisible()
  await page.getByLabel('Full name').fill('Campaign Attendee')
  await page.getByLabel('Email address').fill('attendee@biletflow.dev')
  // 5000 KZT minus 20% = 4000 KZT; the currency format depends on the browser's Intl data.
  await page.getByRole('button', { name: /^Reserve for .*4,?000.* and go to payment$/ }).click()
  await page.waitForURL(/\/orders$/)
  await page
    .getByRole('button', { name: /^Pay .*4,?000.* \(simulation\)$/ })
    .first()
    .click()

  await page.waitForURL(/\/tickets\?order_id=/)
  await expect(page.getByText('Valid', { exact: true })).toBeVisible()

  const orderId = new URL(page.url()).searchParams.get('order_id')
  const attendee = await apiToken(request, 'attendee@biletflow.dev')
  const order = await api(request, 'get', `/orders/detail?order_id=${orderId}`, attendee)
  expect(order.discount_kzt).toBe(100000)
  expect(order.total_amount_kzt).toBe(400000)
  expect(order.promo_campaign_id).toBe(campaign.id)

  const analytics = await api(request, 'get', `/analytics/event?event_id=${event.id}`, organizer)
  const [campaignSales] = analytics.campaigns
  expect(campaignSales.redemptions).toBe(1)
  expect(campaignSales.discounts).toBe(100000)
})

// SRS §1.2 / §2.3: the organizer assigns check-in staff, who then sees the event in the app.
test('organizer assigns check-in staff by email', async ({ page, request }) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  const { event } = await publishedEvent(request, organizer, {
    title: `Staffed Event ${Date.now()}`,
    price: 0,
  })

  await signIn(page, 'organizer@biletflow.dev', PASSWORD)
  await page.goto(`/organizer/events/edit?event_id=${event.id}`)
  await page.getByLabel("Staff member's email").fill('EventAdmin@biletflow.dev')
  await page.getByRole('button', { name: 'Assign' }).click()
  await expect(page.getByText('eventadmin@biletflow.dev')).toBeVisible()

  const staff = await apiToken(request, 'eventadmin@biletflow.dev')
  const assigned = await api(request, 'get', '/checkin/events', staff)
  expect(assigned.map((e: { id: string }) => e.id)).toContain(event.id)

  await page.getByRole('button', { name: 'Remove eventadmin@biletflow.dev' }).click()
  await expect(page.getByText('No staff assigned yet.')).toBeVisible()
})

// SRS §4.2: a private event is reachable only through the organizer's secret link.
test('attendee registers for a private event through its secret link', async ({
  page,
  request,
}) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  const { event } = await publishedEvent(request, organizer, {
    title: `Private Dinner ${Date.now()}`,
    price: 0,
  })
  await api(request, 'patch', `/events/update?event_id=${event.id}`, organizer, {
    visibility: 'private',
  })
  const { link } = await api(request, 'get', `/events/access-link?event_id=${event.id}`, organizer)

  await signIn(page, 'attendee@biletflow.dev', PASSWORD)
  // Without the secret the event does not exist for the attendee.
  const hidden = await request.get(`/api/v1/events/detail?event_id=${event.id}`)
  expect(hidden.status()).toBe(404)

  const url = new URL(link)
  await page.goto(`${url.pathname}${url.search}`)
  await page.getByRole('link', { name: 'Get tickets' }).click()
  await page.getByLabel('Full name').fill('Private Guest')
  await page.getByLabel('Email address').fill('attendee@biletflow.dev')
  await page.getByRole('button', { name: 'Complete free registration' }).click()
  await page.waitForURL(/\/tickets\?order_id=/)
  await expect(page.getByText('Valid', { exact: true })).toBeVisible()

  // SRS §4.13: support opened from the ticket carries the ticket and order.
  await page.getByRole('link', { name: 'Contact support' }).first().click()
  await expect(page.getByText(/Order #.* · Ticket #/)).toBeVisible()
  await page.getByLabel('Subject').fill('Dress code')
  await page.getByLabel('Message').fill('Is there a dress code?')
  await page.getByRole('button', { name: 'Send request' }).click()
  await page.waitForURL(/\/support\/case\?case_id=/)
  await expect(page.getByText(/Ticket #.* · Standard · Valid/)).toBeVisible()
})

// SRS §4.14: the campaign's code also works when the attendee types it at checkout.
test('attendee types a promo code at checkout', async ({ page, request }) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  const { event, start } = await publishedEvent(request, organizer, {
    title: `Typed Code Concert ${Date.now()}`,
    price: 500000,
  })
  await activatePaidSales(request, organizer, event.id)
  const campaign = await api(request, 'post', `/promo/campaigns?event_id=${event.id}`, organizer, {
    name: 'Radio',
    discount_type: 'fixed',
    discount_value: 150000,
    end_time: start.toISOString(),
  })

  await signIn(page, 'attendee@biletflow.dev', PASSWORD)
  await page.goto(`/checkout?event_id=${event.id}`)
  await page.getByLabel('Promo code').fill('WRONG123')
  await page.getByRole('button', { name: 'Apply' }).click()
  await expect(page.getByText('There is no such promo code for this event.')).toBeVisible()

  // Codes are case-insensitive; Enter applies instead of placing the order.
  await page.getByLabel('Promo code').fill(campaign.code.toLowerCase())
  await page.getByLabel('Promo code').press('Enter')
  await expect(page.getByText(`Promo code ${campaign.code}`)).toBeVisible()
  await expect(page).toHaveURL(/\/checkout\?/)

  await page.getByLabel('Full name').fill('Radio Listener')
  await page.getByLabel('Email address').fill('attendee@biletflow.dev')
  // 5000 KZT minus 1500 KZT.
  await page.getByRole('button', { name: /^Reserve for .*3,?500.* and go to payment$/ }).click()
  await page.waitForURL(/\/orders$/)
  await page
    .getByRole('button', { name: /^Pay .*3,?500.* \(simulation\)$/ })
    .first()
    .click()
  await page.waitForURL(/\/tickets\?order_id=/)

  const orderId = new URL(page.url()).searchParams.get('order_id')
  const attendee = await apiToken(request, 'attendee@biletflow.dev')
  const order = await api(request, 'get', `/orders/detail?order_id=${orderId}`, attendee)
  expect(order.discount_kzt).toBe(150000)
  expect(order.promo_campaign_id).toBe(campaign.id)
})

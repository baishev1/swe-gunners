import { expect, test } from '@playwright/test'
import type { APIRequestContext } from '@playwright/test'

import {
  PASSWORD,
  activatePaidSales,
  api,
  apiToken,
  createVerifyToken,
  publishedEvent,
  signIn,
} from './support.ts'

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

// SRS §11 #8: the admission scanner rejects Campaign QR Codes and keeps accepting tickets.
test('scanner rejects a campaign QR and still admits a valid ticket', async ({ request }) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  const eventAdmin = await apiToken(request, 'eventadmin@biletflow.dev')
  const attendee = await apiToken(request, 'attendee@biletflow.dev')
  const { event, ticketType, start } = await publishedEvent(request, organizer, {
    title: `Scanner Check ${Date.now()}`,
    price: 500000,
  })
  await activatePaidSales(request, organizer, event.id)
  const campaign = await api(request, 'post', `/promo/campaigns?event_id=${event.id}`, organizer, {
    name: 'Flyers',
    discount_type: 'percent',
    discount_value: 10,
    end_time: start.toISOString(),
    max_redemptions: 10,
    ticket_type_ids: [ticketType.id],
  })
  const staffUser = await api(request, 'get', '/auth/me', eventAdmin)
  await api(request, 'post', `/checkin/staff?event_id=${event.id}`, organizer, {
    user_id: staffUser.id,
    can_undo_check_in: false,
    can_manage_support: false,
  })
  const order = await api(request, 'post', '/orders', attendee, {
    event_id: event.id,
    customer_name: 'Scanner Attendee',
    customer_email: 'attendee@biletflow.dev',
    items: [{ ticket_type_id: ticketType.id, quantity: 1 }],
  })
  await api(request, 'post', '/payments/simulate', attendee, { order_id: order.id })
  const [ticket] = await api(request, 'get', `/tickets?order_id=${order.id}`, attendee)

  const scan = (payload: string) =>
    api(
      request,
      'get',
      `/tickets/verify?event_id=${event.id}&qr_token=${encodeURIComponent(payload)}`,
      eventAdmin,
    )
  // The Campaign QR encodes the campaign link; the token and the printed code must fail too.
  const campaignToken = String(new URL(campaign.link).searchParams.get('promo'))
  for (const payload of [campaign.link, campaignToken, campaign.code]) {
    const result = await scan(payload)
    expect(result.valid, payload).toBe(false)
    expect(result.ticket).toBeNull()
  }

  expect((await scan(ticket.qr_token)).valid).toBe(true)
  const checkIn = `/api/v1/tickets/check-in?event_id=${event.id}&ticket_id=${ticket.id}`
  expect((await request.post(checkIn, { headers: eventAdmin })).status()).toBe(200)
})

// SRS §11 #12: an administrator suspends a suspicious event and further sales stop.
test('admin suspends an event from the portal and sales stop', async ({ page, request }) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  const title = `Suspicious Event ${Date.now()}`
  const { event, ticketType } = await publishedEvent(request, organizer, { title, price: 0 })

  await signIn(page, 'admin@biletflow.dev', PASSWORD)
  await page.goto('/admin')
  await page.getByRole('tab', { name: 'Events' }).click()
  await page.getByLabel('Event title').fill(title)
  await page.getByRole('button', { name: 'Search' }).click()
  const row = page.getByRole('row').filter({ hasText: title })
  page.once('dialog', (dialog) => dialog.accept())
  await row.getByRole('button', { name: 'Suspend' }).click()
  await expect(row.getByText('Suspended', { exact: true })).toBeVisible()

  const attendee = await apiToken(request, 'attendee@biletflow.dev')
  const blocked = await request.post('/api/v1/orders', {
    headers: attendee,
    data: {
      event_id: event.id,
      customer_name: 'Late Attendee',
      customer_email: 'attendee@biletflow.dev',
      items: [{ ticket_type_id: ticketType.id, quantity: 1 }],
    },
  })
  expect(blocked.status()).toBe(400)

  await page.evaluate(() => localStorage.clear())
  await signIn(page, 'attendee@biletflow.dev', PASSWORD)
  await page.goto(`/events/detail?event_id=${event.id}`)
  // React Query retries the 404 three times before the page shows the error.
  await expect(page.getByText('Event not found')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByRole('link', { name: 'Get tickets' })).toBeHidden()
})

async function paidOrder(
  request: APIRequestContext,
  attendee: Record<string, string>,
  eventId: string,
  ticketTypeId: string,
  customerName: string,
) {
  const order = await api(request, 'post', '/orders', attendee, {
    event_id: eventId,
    customer_name: customerName,
    customer_email: 'attendee@biletflow.dev',
    items: [{ ticket_type_id: ticketTypeId, quantity: 1 }],
  })
  await api(request, 'post', '/payments/simulate', attendee, { order_id: order.id })
  return order
}

// SRS §11 #2: an organizer completes the simulated paid-sales activation and receives
// demonstration orders.
test('new organizer activates paid sales and receives an order', async ({ page, request }) => {
  const email = `organizer-${Date.now()}@example.com`
  const user = await api(
    request,
    'post',
    '/auth/register',
    {},
    {
      email,
      password: PASSWORD,
      full_name: 'Fresh Organizer',
      role: 'organizer',
    },
  )
  await api(request, 'post', '/auth/verify-email', {}, { token: createVerifyToken(user.id) })
  const organizer = await apiToken(request, email)
  const { event, ticketType } = await publishedEvent(request, organizer, {
    title: `Activation ${Date.now()}`,
    price: 500000,
  })

  // Paid tickets cannot be sold before activation.
  const attendee = await apiToken(request, 'attendee@biletflow.dev')
  const early = await request.post('/api/v1/orders', {
    headers: attendee,
    data: {
      event_id: event.id,
      customer_name: 'Early Buyer',
      customer_email: 'attendee@biletflow.dev',
      items: [{ ticket_type_id: ticketType.id, quantity: 1 }],
    },
  })
  expect(early.ok()).toBeFalsy()

  await signIn(page, email, PASSWORD)
  await page.goto('/organizer/profile')
  await page.getByLabel('Recipient name').fill('Fresh Events LLP')
  await page.getByLabel('IBAN').fill('KZ86125KZT5004100100')
  await page.getByLabel('BIN / IIN').fill('123456789012')
  await page.getByRole('button', { name: 'Save' }).click()
  await expect(page.getByText('Saved.')).toBeVisible()

  await page.goto(`/organizer/events/edit?event_id=${event.id}`)
  const checklist = page.getByRole('list', { name: 'Activation checklist' })
  await checklist.getByRole('button', { name: 'Verify identity (demo)' }).click()
  await checklist.getByRole('button', { name: 'Pay fee (demo)' }).click()
  await checklist.getByRole('button', { name: 'Accept terms' }).click()
  await page.getByRole('button', { name: 'Activate paid sales' }).click()
  await expect(page.getByText(/^Paid sales are active/)).toBeVisible()

  await paidOrder(request, attendee, event.id, ticketType.id, 'Demo Buyer')
  await page.reload()
  const row = page.getByRole('row').filter({ hasText: 'Demo Buyer' })
  await expect(row.getByText('Paid', { exact: true })).toBeVisible()
})

// SRS §11 #9 and #10: organizers see accurate ticket, attendance, payment and refund
// records, and the analytics built from them.
test('organizer refunds an order and the records and analytics agree', async ({
  page,
  request,
}) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  const eventAdmin = await apiToken(request, 'eventadmin@biletflow.dev')
  const attendee = await apiToken(request, 'attendee@biletflow.dev')
  const { event, ticketType } = await publishedEvent(request, organizer, {
    title: `Records ${Date.now()}`,
    price: 500000,
  })
  await activatePaidSales(request, organizer, event.id)
  const staffUser = await api(request, 'get', '/auth/me', eventAdmin)
  await api(request, 'post', `/checkin/staff?event_id=${event.id}`, organizer, {
    user_id: staffUser.id,
    can_undo_check_in: false,
    can_manage_support: false,
  })

  const arrived = await paidOrder(request, attendee, event.id, ticketType.id, 'Arrived Guest')
  await paidOrder(request, attendee, event.id, ticketType.id, 'Refunded Guest')
  const [ticket] = await api(request, 'get', `/tickets?order_id=${arrived.id}`, attendee)
  await api(
    request,
    'post',
    `/tickets/check-in?event_id=${event.id}&ticket_id=${ticket.id}`,
    eventAdmin,
  )

  await signIn(page, 'organizer@biletflow.dev', PASSWORD)
  await page.goto(`/organizer/events/edit?event_id=${event.id}`)
  const refunded = page.getByRole('row').filter({ hasText: 'Refunded Guest' })
  await refunded.getByRole('button', { name: 'Refund' }).click()
  await refunded.getByRole('button', { name: 'Confirm refund' }).click()
  await expect(refunded.getByText('Refunded', { exact: true })).toBeVisible()
  const paid = page.getByRole('row').filter({ hasText: 'Arrived Guest' })
  await expect(paid.getByText('Paid', { exact: true })).toBeVisible()

  await page.goto(`/organizer/events/attendees?event_id=${event.id}`)
  await expect(
    page
      .getByRole('row')
      .filter({ hasText: 'Arrived Guest' })
      .getByRole('cell', { name: 'Checked in', exact: true }),
  ).toBeVisible()
  await expect(
    page
      .getByRole('row')
      .filter({ hasText: 'Refunded Guest' })
      .getByRole('cell', { name: 'Refunded', exact: true }),
  ).toBeVisible()

  await page.goto(`/organizer/events/analytics?event_id=${event.id}`)
  // Stat cards use a <span> label; the ticket type table repeats the same words in <th>.
  const stat = (label: string) =>
    page.getByText(label, { exact: true }).and(page.locator('span')).locator('..')
  await expect(stat('Sold')).toContainText('1')
  await expect(stat('Gross sales')).toContainText(/10,?000/)
  await expect(stat('Refunds')).toContainText(/5,?000/)
  await expect(stat('Checked in')).toContainText('1')

  // Attendee checkout asks for name and email only (SRS §11 #10).
  await page.goto(`/checkout?event_id=${event.id}`)
  const attendeeCard = page
    .locator('[data-slot="card"]')
    .filter({ has: page.getByText('Attendee information', { exact: true }) })
  await expect(attendeeCard.getByRole('textbox')).toHaveCount(2)
})

// SRS §11 #11: organizers review cancelled events, inspect the activity timeline and
// duplicate an event without copying its transactions.
test('organizer reviews a cancelled event and duplicates it without orders', async ({
  page,
  request,
}) => {
  const organizer = await apiToken(request, 'organizer@biletflow.dev')
  const attendee = await apiToken(request, 'attendee@biletflow.dev')
  const title = `Cancelled Gig ${Date.now()}`
  const { event, ticketType } = await publishedEvent(request, organizer, { title, price: 0 })
  await api(request, 'post', '/orders', attendee, {
    event_id: event.id,
    customer_name: 'Early Fan',
    customer_email: 'attendee@biletflow.dev',
    items: [{ ticket_type_id: ticketType.id, quantity: 1 }],
  })
  await api(request, 'post', `/events/cancel?event_id=${event.id}`, organizer)

  await signIn(page, 'organizer@biletflow.dev', PASSWORD)
  await page.goto('/organizer/events')
  await page.getByRole('tab', { name: 'Cancelled' }).click()
  const card = page.getByRole('listitem').filter({ hasText: title })
  await card.getByRole('link', { name: 'History' }).click()
  // A string filter ignores case, and "Published event Cancelled Gig" would match.
  const entry = (action: string) =>
    page.getByRole('listitem').filter({ hasText: new RegExp(action) })
  await expect(entry('Event published')).toBeVisible()
  // Cancelling closes the free registration too, and the history keeps it.
  await expect(entry('Order cancelled')).toBeVisible()
  await expect(entry('Event cancelled')).toBeVisible()

  await page.goto('/organizer/events')
  await page.getByRole('tab', { name: 'Cancelled' }).click()
  await card.getByRole('button', { name: 'Duplicate' }).click()
  await page.waitForURL((url) => {
    const id = url.searchParams.get('event_id')
    return url.pathname === '/organizer/events/edit' && id !== null && id !== event.id
  })

  const copyId = String(new URL(page.url()).searchParams.get('event_id'))
  const copy = await api(request, 'get', `/events/detail?event_id=${copyId}`, organizer)
  expect(copy.title).toBe(`${title} (Copy)`)
  expect(copy.status).toBe('draft')
  expect(await api(request, 'get', `/orders/manage?event_id=${copyId}`, organizer)).toEqual([])
  const original = await api(request, 'get', `/orders/manage?event_id=${event.id}`, organizer)
  expect(original).toHaveLength(1)
})

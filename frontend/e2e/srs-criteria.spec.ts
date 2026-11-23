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
  await page.getByRole('link', { name: 'Get tickets' }).click()

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
  await page.getByRole('button', { name: /^Pay .*4,?000.* \(simulation\)$/ }).click()

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

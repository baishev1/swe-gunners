import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

import { activatePaidSales, api, apiToken, publishedEvent } from './support.ts'

// SRS §7: event pages should meet WCAG 2.1 AA.
const WCAG_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']

async function expectNoViolations(page: Page) {
  const { violations } = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze()
  const summary = violations.map((v) => ({
    rule: v.id,
    impact: v.impact,
    help: v.help,
    targets: v.nodes.map((n) => n.target.join(' ')),
  }))
  expect(summary, JSON.stringify(summary, null, 2)).toEqual([])
}

for (const language of ['ru', 'kk', 'en']) {
  test(`buyer pages pass axe WCAG 2.1 AA checks (${language})`, async ({ page, request }) => {
    await page.addInitScript((lang) => localStorage.setItem('language', lang), language)
    const organizer = await apiToken(request, 'organizer@biletflow.dev')
    const { event } = await publishedEvent(request, organizer, {
      title: `A11y Concert ${language} ${Date.now()}`,
      price: 500000,
    })
    await activatePaidSales(request, organizer, event.id)

    await page.goto(`/events/detail?event_id=${event.id}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    await expectNoViolations(page)

    // Sign in by token: the login form labels change with the language under test.
    const attendee = await apiToken(request, 'attendee@biletflow.dev')
    const token = attendee.Authorization.replace('Bearer ', '')
    await page.evaluate((value) => localStorage.setItem('access_token', value), token)
    await page.goto(`/checkout?event_id=${event.id}`)
    await expect(page.locator('form')).toBeVisible()
    await expectNoViolations(page)

    // Campaign link: the event page banner and the checkout discount rows.
    const campaign = await api(
      request,
      'post',
      `/promo/campaigns?event_id=${event.id}`,
      organizer,
      {
        name: 'A11y',
        discount_type: 'percent',
        discount_value: 10,
      },
    )
    const link = new URL(campaign.link)
    await page.goto(`${link.pathname}${link.search}`)
    await expect(page.getByRole('status').filter({ hasText: campaign.code })).toBeVisible()
    await expectNoViolations(page)
    await page.goto(`/checkout?event_id=${event.id}`)
    await expect(page.getByText(campaign.code)).toBeVisible()
    await expectNoViolations(page)

    const [ticketType] = await api(request, 'get', `/ticket-types?event_id=${event.id}`, attendee)
    const order = await api(request, 'post', '/orders', attendee, {
      event_id: event.id,
      customer_name: 'A11y Attendee',
      customer_email: 'attendee@biletflow.dev',
      items: [{ ticket_type_id: ticketType.id, quantity: 1 }],
    })
    await api(request, 'post', '/payments/simulate', attendee, {
      order_id: order.id,
      simulate_failure: false,
    })
    await page.goto(`/tickets?order_id=${order.id}`)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    await expectNoViolations(page)

    await page.goto('/orders')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    await expectNoViolations(page)
  })
}

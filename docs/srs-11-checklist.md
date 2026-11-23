# SRS §11 demo checklist

Manual run of the 12 MVP success criteria on the deployed server, before the
demonstration. Run it after a fresh `make seed` (or
`docker compose exec backend python -m scripts.seed`): every step below uses
the seeded data, so nothing has to be prepared by hand.

All demo accounts use the password `password123`.

| Account | Role |
|---|---|
| `attendee@biletflow.dev` | Attendee |
| `organizer@biletflow.dev` | Organizer of all seeded events |
| `eventadmin@biletflow.dev` | Event Admin (mobile app), assigned to the concert, the lecture and the jazz evening |
| `admin@biletflow.dev` | Platform Admin |

Seeded events: **Открытая лекция** (free), **BiletFlow Demo Concert** (paid,
promo code `DEMO20`), **Jazz Evening Almaty** (completed), **Outdoor Cinema
Night** (cancelled, refunded).

Tick each box only after doing it on the server, not locally. Write anything
that goes wrong under [Bugs found](#bugs-found).

Automated coverage: `frontend/e2e/` already runs #1, #3, #5, #6, #7, #8 and #12
against the API and web app in CI. The manual run still matters for the
mobile app, printing and the deployed environment.

## Criteria

### 1. Organizer publishes a free event and distributes valid tickets
- [ ] As the organizer, create an event with a free ticket type, preview it, publish it.
- [ ] As the attendee, open it, choose **Get tickets**, complete the free registration.
- [ ] The ticket shows status **Valid**; the organizer sees the attendee in the attendee list.

### 2. Organizer completes simulated paid-sales activation and receives demo orders
- [ ] As the organizer, create a paid ticket type on a new event and open the activation checklist.
- [ ] Complete identity check, payout account, fee and terms; activate.
- [ ] Every payment screen is labelled as a simulation.
- [ ] As the attendee, buy a ticket; the order appears under the organizer's orders.

### 3. Attendee completes checkout and receives a QR-code ticket
- [ ] As the attendee, buy a General admission ticket for **BiletFlow Demo Concert**.
- [ ] The confirmation email arrives (check Mailpit or the SMTP inbox).
- [ ] **My tickets** shows the ticket with its QR code.

### 4. Attendee downloads and prints a ticket that scans at check-in
- [ ] Download the PDF from **My tickets**.
- [ ] Print it on A4 **in black and white**.
- [ ] Event name, date and time, venue, ticket type, attendee name, ticket ID and QR are all readable; no payment data is printed.
- [ ] Scan the **paper** QR with the mobile app: result is valid.

### 5. Event Admin validates tickets and prevents duplicate entry
- [ ] Sign in to the mobile app as `eventadmin@biletflow.dev`; only assigned events are listed.
- [ ] Scan a valid ticket: valid, check-in recorded.
- [ ] Scan the same ticket again: already used.
- [ ] Undo the check-in, scan again: valid.
- [ ] Scan a refunded ticket from **Outdoor Cinema Night**: refunded / invalid.
- [ ] Manual attendee search finds the attendee; registered and checked-in counters update.

### 6. Attendee opens a contextual support case and exchanges messages
- [ ] As the attendee, open **Contact support** from an order or ticket; pick a category, send a message.
- [ ] The case shows the event / order / ticket context.
- [ ] As the organizer, reply and change the status; the attendee sees the reply and gets an email.
- [ ] Another attendee cannot open the case.

### 7. Attendee scans a Campaign QR Code, gets the discount, order is attributed
- [ ] As the organizer, open the concert's promo campaigns and show the Campaign QR.
- [ ] Scan it with a phone camera: the event page opens with the code applied.
- [ ] Checkout shows the code, the discount and the new total before paying.
- [ ] After paying, the campaign's redemption count and revenue go up in analytics.

### 8. Admission scanner rejects Campaign QR Codes, accepts ticket QR codes
- [ ] Scan the Campaign QR with the mobile app: rejected, no check-in.
- [ ] Scan a real ticket right after: accepted.

### 9. Organizer views accurate ticket, attendance, payment and refund records
- [ ] For the concert, numbers in orders, attendee list and ticket-type counters agree.
- [ ] For **Outdoor Cinema Night**, both orders show as refunded and tickets as refunded.

### 10. Organizer views sales, capacity, campaign and attendance analytics
- [ ] Concert analytics: capacity, sold, remaining, gross, discounts, net in KZT; sales over time has several days; campaign `DEMO20` shows redemptions.
- [ ] Jazz Evening analytics: checked-in, absent and check-in percentage.
- [ ] Checkout never asked for extra attendee fields.

### 11. Organizer reviews past and cancelled events, timeline, duplicates without transactions
- [ ] The dashboard lists Jazz Evening under Completed and Outdoor Cinema under Cancelled.
- [ ] Each timeline shows publication, ticket types, activation, check-ins, cancellation, refunds; filter by date and type works.
- [ ] Duplicate Jazz Evening: the new draft has no orders, tickets or check-ins.

### 12. Administrator suspends a suspicious event and stops further sales
- [ ] As the admin, suspend a published event.
- [ ] As the attendee, try to buy: refused. The event no longer sells.

## Non-functional spot checks
- [ ] Customer pages work in Kazakh, Russian and English (switcher top right).
- [ ] Phone browser: event, checkout and tickets pages fit the screen.
- [ ] QR validation in the app answers within about two seconds.
- [ ] HTTPS on the server; demo payments are never shown as real transactions.

## Bugs found

Known before the manual run (found while preparing it):

- **The on-screen ticket has no real QR code.** `TicketCard` shows a generic
  QR icon and the first characters of the token; only the PDF carries the
  scannable code. Criterion #3 ("receive a QR-code ticket") and scanning a
  ticket from a phone screen fail until the card renders the real QR.
- The fixed language switcher overlaps the header button on **My tickets** and
  **My orders** at narrow widths (the home page was fixed separately).
- In Kazakh, the browser formats dates as "2026 M11 23" and prices as
  "KZT 50.00": limited `kk` locale data in browsers, not a translation gap.
- A promo code can only be applied through a Campaign QR link; there is no
  field to type a code at checkout.
- Error messages on organizer and admin pages still come from the API in
  English (buyer pages are translated).

Found during the run:

| # | Criterion | What happened | Who | Fixed in |
|---|---|---|---|---|
| | | | | |

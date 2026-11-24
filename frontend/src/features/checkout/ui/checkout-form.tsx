import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { isAxiosError } from 'axios'
import { useNavigate } from 'react-router-dom'
import { createOrder } from '@/shared/api'
import { Button, Card, CardContent, CardFooter, CardHeader, CardTitle, Input } from '@/shared/ui'
import { formatPrice } from '@/shared/lib/format'
import type { OrderItemCreate } from '@/shared/types'
import type { ResolvedPromo } from '@/entities/promo-campaign'
import { type SelectedSeat, seatLabel } from '@/entities/seating'

import { PromoCodeField } from './promo-code-field'

export interface CheckoutTicketTypeOption {
  id: string
  name: string
  price_kzt: number
  available: number
  max_per_order: number | null
}

// The most of one ticket type a single order can take right now.
function maxQuantity(type: CheckoutTicketTypeOption) {
  return type.max_per_order ? Math.min(type.available, type.max_per_order) : type.available
}

interface CheckoutFormProps {
  eventId: string
  ticketTypes: CheckoutTicketTypeOption[]
  promo?: ResolvedPromo | null
  onRemovePromo?: () => void
  /** Applies a typed promo code; without it the field is hidden. */
  onApplyPromo?: (code: string) => Promise<void>
  /** Secret from a private event's link; the server checks it again (SRS 4.2). */
  accessToken?: string | null
  /** Assigned-seating events pass the picked seats instead of quantities (SRS 4.3.1). */
  seats?: SelectedSeat[]
  /** Called when a seat was taken by someone else, so the map can refresh. */
  onSeatConflict?: () => void
}

// Preview only: the server recalculates the discount when it creates the order (SRS 4.14).
function previewDiscount(promo: ResolvedPromo, eligibleSubtotal: number) {
  if (promo.discount_type === 'percent') {
    return Math.floor((eligibleSubtotal * promo.discount_value) / 100)
  }
  return Math.min(promo.discount_value, eligibleSubtotal)
}

// Backend error details are English, so buyer-facing messages come from the locale files.
function checkoutErrorKey(error: unknown, seated: boolean) {
  const status = isAxiosError(error) ? error.response?.status : undefined
  if (status === 400) return 'checkout.errors.notAvailable'
  if (status === 403) return 'checkout.errors.salesClosed'
  if (status === 409) return seated ? 'checkout.errors.seatTaken' : 'checkout.errors.soldOut'
  return 'checkout.errors.generic'
}

export function CheckoutForm({
  eventId,
  ticketTypes,
  promo,
  onRemovePromo,
  onApplyPromo,
  accessToken,
  seats,
  onSeatConflict,
}: CheckoutFormProps) {
  const seated = seats !== undefined
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [quantities, setQuantities] = useState<Record<string, number>>(() => {
    const firstOnSale = ticketTypes.find((t) => t.available > 0)
    return Object.fromEntries(ticketTypes.map((t) => [t.id, t === firstOnSale ? 1 : 0]))
  })
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleQuantityChange = (type: CheckoutTicketTypeOption, delta: number) => {
    setQuantities((prev) => {
      const next = Math.min(maxQuantity(type), Math.max(0, (prev[type.id] || 0) + delta))
      return { ...prev, [type.id]: next }
    })
  }

  // One line per ticket type: picked quantities, or the seats grouped by their ticket type.
  const lines = seated
    ? ticketTypes
        .map((t) => ({ type: t, seats: seats.filter((s) => s.ticketTypeId === t.id) }))
        .filter((l) => l.seats.length > 0)
        .map((l) => ({
          ticketTypeId: l.type.id,
          quantity: l.seats.length,
          amount: l.seats.reduce((sum, s) => sum + s.price, 0),
          seats: l.seats.map((s) => s.id),
        }))
    : ticketTypes
        .filter((t) => (quantities[t.id] || 0) > 0)
        .map((t) => ({
          ticketTypeId: t.id,
          quantity: quantities[t.id],
          amount: t.price_kzt * quantities[t.id],
          seats: undefined,
        }))

  const selectedItems: OrderItemCreate[] = lines.map((l) => ({
    ticket_type_id: l.ticketTypeId,
    quantity: l.quantity,
    ...(l.seats ? { seats: l.seats } : {}),
  }))

  const subtotalKzt = lines.reduce((sum, l) => sum + l.amount, 0)
  const discountKzt = promo
    ? previewDiscount(
        promo,
        lines
          .filter(
            (l) =>
              promo.ticket_type_ids.length === 0 || promo.ticket_type_ids.includes(l.ticketTypeId),
          )
          .reduce((sum, l) => sum + l.amount, 0),
      )
    : 0
  const totalAmountKzt = subtotalKzt - discountKzt

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!customerName.trim() || !customerEmail.trim()) {
      setErrorMessage(t('checkout.errors.missingDetails'))
      return
    }

    if (selectedItems.length === 0) {
      setErrorMessage(t(seated ? 'checkout.errors.noSeats' : 'checkout.errors.noTickets'))
      return
    }

    setIsLoading(true)
    try {
      const order = await createOrder({
        event_id: eventId,
        customer_name: customerName,
        customer_email: customerEmail,
        items: selectedItems,
        promo_code: promo?.code ?? null,
        access_token: accessToken ?? null,
      })

      // Free orders are confirmed at once. Paid ones stay reserved (pending) until the
      // attendee pays from My orders, so an abandoned checkout releases its hold (SRS 4.6).
      navigate(order.status === 'paid' ? `/tickets?order_id=${order.id}` : '/orders')
    } catch (err: unknown) {
      setErrorMessage(t(checkoutErrorKey(err, seated)))
      if (seated && isAxiosError(err) && err.response?.status === 409) onSeatConflict?.()
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>{t(seated ? 'checkout.selectedSeats' : 'checkout.selectTickets')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {seated && seats.length === 0 && (
            <p className="text-muted-foreground text-sm">{t('seating.noneSelected')}</p>
          )}
          {seated && (
            <ul className="space-y-1.5">
              {seats.map((seat) => (
                <li key={seat.id} className="flex justify-between gap-2 text-sm">
                  <span>{seatLabel(t, seat.id)}</span>
                  <span className="text-muted-foreground shrink-0">{formatPrice(seat.price)}</span>
                </li>
              ))}
            </ul>
          )}
          {!seated &&
            ticketTypes.map((type) => (
              <div
                key={type.id}
                className="flex items-center justify-between border-b pb-3 last:border-0"
              >
                <div>
                  <p className="font-medium text-sm text-foreground">{type.name}</p>
                  <p className="text-muted-foreground text-xs">
                    {formatPrice(type.price_kzt)} ·{' '}
                    {type.available > 0
                      ? t('checkout.remaining', { count: type.available })
                      : t('checkout.soldOut')}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon-xs"
                    aria-label={t('checkout.decrease', { name: type.name })}
                    onClick={() => handleQuantityChange(type, -1)}
                    disabled={isLoading || (quantities[type.id] || 0) === 0}
                  >
                    -
                  </Button>
                  <span className="w-6 text-center text-sm font-semibold">
                    {quantities[type.id] || 0}
                  </span>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon-xs"
                    aria-label={t('checkout.increase', { name: type.name })}
                    onClick={() => handleQuantityChange(type, 1)}
                    disabled={isLoading || (quantities[type.id] || 0) >= maxQuantity(type)}
                  >
                    +
                  </Button>
                </div>
              </div>
            ))}

          {promo && (
            <div className="space-y-1 border-t pt-2 text-sm">
              <div className="flex justify-between text-muted-foreground">
                <span>{t('checkout.subtotal')}</span>
                <span>{formatPrice(subtotalKzt)}</span>
              </div>
              <div className="flex items-center justify-between gap-2" role="status">
                <span className="flex items-center gap-2">
                  {t('checkout.promoApplied', { code: promo.code })}
                  {onRemovePromo && (
                    <Button
                      type="button"
                      variant="link"
                      size="sm"
                      className="h-auto p-0"
                      onClick={onRemovePromo}
                      disabled={isLoading}
                    >
                      {t('checkout.removePromo')}
                    </Button>
                  )}
                </span>
                <span>−{formatPrice(discountKzt)}</span>
              </div>
              {subtotalKzt > 0 && discountKzt === 0 && (
                <p className="text-xs text-muted-foreground">
                  {t('checkout.promoCode.notApplicable')}
                </p>
              )}
            </div>
          )}
          {!promo && onApplyPromo && <PromoCodeField onApply={onApplyPromo} disabled={isLoading} />}

          <div className="flex justify-between pt-2 border-t font-semibold text-base">
            <span>{t('checkout.total')}</span>
            <span>{formatPrice(totalAmountKzt)}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('checkout.attendeeInfo')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="checkout-name" className="text-xs font-medium text-muted-foreground">
              {t('checkout.fullName')}
            </label>
            <Input
              id="checkout-name"
              autoComplete="name"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder={t('checkout.fullNamePlaceholder')}
              required
              disabled={isLoading}
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="checkout-email" className="text-xs font-medium text-muted-foreground">
              {t('checkout.email')}
            </label>
            <Input
              id="checkout-email"
              autoComplete="email"
              type="email"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              placeholder={t('checkout.emailPlaceholder')}
              required
              disabled={isLoading}
            />
          </div>

          {totalAmountKzt > 0 && (
            <div className="rounded-md border p-3 bg-muted/20 text-xs text-muted-foreground space-y-2">
              <p className="font-semibold text-foreground">{t('checkout.simulationTitle')}</p>
              <p>{t('checkout.holdNote')}</p>
            </div>
          )}

          {errorMessage && (
            <div className="rounded-md bg-destructive/10 p-3 text-xs text-destructive">
              {errorMessage}
            </div>
          )}
        </CardContent>
        <CardFooter>
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || (seated && seats.length === 0)}
          >
            {isLoading
              ? t('checkout.processing')
              : totalAmountKzt === 0
                ? t('checkout.registerFree')
                : t('checkout.reserve', { amount: formatPrice(totalAmountKzt) })}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}

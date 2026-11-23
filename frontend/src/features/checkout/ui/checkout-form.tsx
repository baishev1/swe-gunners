import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { isAxiosError } from 'axios'
import { useNavigate } from 'react-router-dom'
import { createOrder, simulatePayment } from '@/shared/api'
import { Button, Card, CardContent, CardFooter, CardHeader, CardTitle, Input } from '@/shared/ui'
import { formatPrice } from '@/shared/lib/format'
import type { OrderItemCreate } from '@/shared/types'

export interface CheckoutTicketTypeOption {
  id: string
  name: string
  price_kzt: number
}

interface CheckoutFormProps {
  eventId: string
  ticketTypes: CheckoutTicketTypeOption[]
}

// Backend error details are English, so buyer-facing messages come from the locale files.
function checkoutErrorKey(error: unknown) {
  const status = isAxiosError(error) ? error.response?.status : undefined
  if (status === 400) return 'checkout.errors.notAvailable'
  if (status === 403) return 'checkout.errors.salesClosed'
  if (status === 409) return 'checkout.errors.soldOut'
  return 'checkout.errors.generic'
}

export function CheckoutForm({ eventId, ticketTypes }: CheckoutFormProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [quantities, setQuantities] = useState<Record<string, number>>(
    Object.fromEntries(ticketTypes.map((t, idx) => [t.id, idx === 0 ? 1 : 0])),
  )
  const [simulateFailure, setSimulateFailure] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleQuantityChange = (id: string, delta: number) => {
    setQuantities((prev) => {
      const current = prev[id] || 0
      const next = Math.max(0, current + delta)
      return { ...prev, [id]: next }
    })
  }

  const selectedItems: OrderItemCreate[] = ticketTypes
    .filter((t) => (quantities[t.id] || 0) > 0)
    .map((t) => ({ ticket_type_id: t.id, quantity: quantities[t.id] }))

  const totalAmountKzt = ticketTypes.reduce(
    (sum, t) => sum + t.price_kzt * (quantities[t.id] || 0),
    0,
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!customerName.trim() || !customerEmail.trim()) {
      setErrorMessage(t('checkout.errors.missingDetails'))
      return
    }

    if (selectedItems.length === 0) {
      setErrorMessage(t('checkout.errors.noTickets'))
      return
    }

    setIsLoading(true)
    try {
      const order = await createOrder({
        event_id: eventId,
        customer_name: customerName,
        customer_email: customerEmail,
        items: selectedItems,
      })

      if (totalAmountKzt === 0) {
        navigate(`/tickets?order_id=${order.id}`)
        return
      }

      const payment = await simulatePayment({
        order_id: order.id,
        simulate_failure: simulateFailure,
      })

      if (payment.status === 'succeeded') {
        navigate(`/tickets?order_id=${order.id}`)
      } else {
        setErrorMessage(t('checkout.errors.paymentFailed'))
      }
    } catch (err: unknown) {
      setErrorMessage(t(checkoutErrorKey(err)))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>{t('checkout.selectTickets')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {ticketTypes.map((type) => (
            <div
              key={type.id}
              className="flex items-center justify-between border-b pb-3 last:border-0"
            >
              <div>
                <p className="font-medium text-sm text-foreground">{type.name}</p>
                <p className="text-muted-foreground text-xs">{formatPrice(type.price_kzt)}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="icon-xs"
                  aria-label={t('checkout.decrease', { name: type.name })}
                  onClick={() => handleQuantityChange(type.id, -1)}
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
                  onClick={() => handleQuantityChange(type.id, 1)}
                  disabled={isLoading}
                >
                  +
                </Button>
              </div>
            </div>
          ))}

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
              <p>{t('checkout.simulationNote')}</p>
              <label className="flex items-center gap-2 pt-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={simulateFailure}
                  onChange={(e) => setSimulateFailure(e.target.checked)}
                  className="rounded border-input text-primary focus:ring-primary"
                />
                <span>{t('checkout.simulateFailure')}</span>
              </label>
            </div>
          )}

          {errorMessage && (
            <div className="rounded-md bg-destructive/10 p-3 text-xs text-destructive">
              {errorMessage}
            </div>
          )}
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading
              ? t('checkout.processing')
              : totalAmountKzt === 0
                ? t('checkout.registerFree')
                : t('checkout.pay', { amount: formatPrice(totalAmountKzt) })}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}

import { useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { simulatePayment } from '@/shared/api'
import { formatDateTime, formatPrice } from '@/shared/lib/format'
import type { Order } from '@/shared/types'
import { Button } from '@/shared/ui'

interface PayOrderPanelProps {
  order: Order
}

/** Simulated payment for a reserved (pending) order; no real money moves (SRS 4.6). */
export function PayOrderPanel({ order }: PayOrderPanelProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [simulateFailure, setSimulateFailure] = useState(false)
  const [isPaying, setIsPaying] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const failureId = `simulate-failure-${order.id}`

  const pay = async () => {
    setErrorMessage(null)
    setIsPaying(true)
    try {
      const payment = await simulatePayment({
        order_id: order.id,
        simulate_failure: simulateFailure,
      })
      if (payment.status === 'succeeded') {
        await queryClient.invalidateQueries({ queryKey: ['orders'] })
        navigate(`/tickets?order_id=${order.id}`)
        return
      }
      setErrorMessage(t('checkout.errors.paymentFailed'))
    } catch (err: unknown) {
      // 409: the hold ran out (or the promo code was used up) and the tickets were released.
      const expired = isAxiosError(err) && err.response?.status === 409
      setErrorMessage(t(expired ? 'orders.payment.expired' : 'checkout.errors.generic'))
      if (expired) await queryClient.invalidateQueries({ queryKey: ['orders'] })
    } finally {
      setIsPaying(false)
    }
  }

  return (
    <section
      aria-label={t('orders.payment.title')}
      className="rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground space-y-2"
    >
      <p className="font-semibold text-foreground">{t('orders.payment.title')}</p>
      {order.hold_expires_at && (
        <p>{t('orders.payment.heldUntil', { time: formatDateTime(order.hold_expires_at) })}</p>
      )}
      <p>{t('checkout.simulationNote')}</p>
      <div className="flex items-center gap-2">
        <input
          id={failureId}
          type="checkbox"
          checked={simulateFailure}
          onChange={(e) => setSimulateFailure(e.target.checked)}
          disabled={isPaying}
          className="rounded border-input text-primary focus:ring-primary"
        />
        <label htmlFor={failureId} className="cursor-pointer">
          {t('checkout.simulateFailure')}
        </label>
      </div>
      {errorMessage && (
        <p role="alert" className="rounded-md bg-destructive/10 p-2 text-destructive">
          {errorMessage}
        </p>
      )}
      <Button type="button" className="w-full" onClick={pay} disabled={isPaying}>
        {isPaying
          ? t('checkout.processing')
          : t('checkout.pay', { amount: formatPrice(order.total_amount_kzt) })}
      </Button>
    </section>
  )
}

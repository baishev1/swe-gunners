import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import { useEvent } from '@/entities/event'
import { useTicketTypes } from '@/entities/ticket-type'
import { applyPromoCode, clearAppliedPromo, getAppliedPromo } from '@/features/apply-promo-link'
import { CheckoutForm } from '@/features/checkout'
import { Skeleton } from '@/shared/ui/skeleton'

export function CheckoutPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const eventId = searchParams.get('event_id') ?? ''
  const access = searchParams.get('access')
  const event = useEvent(eventId, access)
  const ticketTypes = useTicketTypes(eventId, false, access)
  // Events without their own policy show the platform default (SRS 4.9).
  const refundPolicy = event.data?.refund_policy?.trim() || t('eventDetail.defaultRefundPolicy')
  const [promo, setPromo] = useState(() => getAppliedPromo(eventId))
  const removePromo = () => {
    clearAppliedPromo(eventId)
    setPromo(null)
  }
  const applyPromo = async (code: string) => setPromo(await applyPromoCode(eventId, code))

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">{t('checkout.title')}</h1>
        <p className="text-muted-foreground text-sm mt-1">{t('checkout.subtitle')}</p>
      </div>
      <div className="mx-auto mb-6 max-w-xl rounded-md border p-4 text-sm">
        <p className="font-medium">{t('eventDetail.refundPolicy')}</p>
        <p className="text-muted-foreground mt-1 whitespace-pre-line">{refundPolicy}</p>
      </div>
      {ticketTypes.isPending ? (
        <Skeleton className="mx-auto h-64 max-w-xl" />
      ) : (
        <CheckoutForm
          eventId={eventId}
          promo={promo}
          accessToken={access}
          onRemovePromo={removePromo}
          onApplyPromo={applyPromo}
          ticketTypes={(ticketTypes.data ?? []).map((t) => ({
            id: t.id,
            name: t.name,
            price_kzt: t.price,
            available: t.available,
            max_per_order: t.max_per_order,
          }))}
        />
      )}
    </div>
  )
}

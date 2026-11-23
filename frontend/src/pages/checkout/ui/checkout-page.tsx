import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import { useEvent } from '@/entities/event'
import { useTicketTypes } from '@/entities/ticket-type'
import { clearAppliedPromo, getAppliedPromo } from '@/features/apply-promo-link'
import { CheckoutForm } from '@/features/checkout'
import { Skeleton } from '@/shared/ui/skeleton'

export function CheckoutPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const eventId = searchParams.get('event_id') ?? ''
  const event = useEvent(eventId)
  const ticketTypes = useTicketTypes(eventId)
  const refundPolicy = event.data?.refund_policy
  const [promo, setPromo] = useState(() => getAppliedPromo(eventId))
  const removePromo = () => {
    clearAppliedPromo(eventId)
    setPromo(null)
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">{t('checkout.title')}</h1>
        <p className="text-muted-foreground text-sm mt-1">{t('checkout.subtitle')}</p>
      </div>
      {refundPolicy && (
        <div className="mx-auto mb-6 max-w-xl rounded-md border p-4 text-sm">
          <p className="font-medium">{t('eventDetail.refundPolicy')}</p>
          <p className="text-muted-foreground mt-1 whitespace-pre-line">{refundPolicy}</p>
        </div>
      )}
      {ticketTypes.isPending ? (
        <Skeleton className="mx-auto h-64 max-w-xl" />
      ) : (
        <CheckoutForm
          eventId={eventId}
          promo={promo}
          onRemovePromo={removePromo}
          ticketTypes={(ticketTypes.data ?? [])
            .filter((t) => t.available > 0)
            .map((t) => ({ id: t.id, name: t.name, price_kzt: t.price }))}
        />
      )}
    </div>
  )
}

import { LifeBuoy } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import type { SupportCategory } from '@/entities/support'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'

interface ContactSupportLinkProps {
  eventId?: string
  /** Attaches the order or ticket the attendee is asking about (SRS 4.13). */
  orderId?: string
  ticketId?: string
  category?: SupportCategory
  className?: string
}

export function ContactSupportLink({
  eventId,
  orderId,
  ticketId,
  category,
  className,
}: ContactSupportLinkProps) {
  const { t } = useTranslation()
  const params = new URLSearchParams()
  if (eventId) params.set('event_id', eventId)
  if (orderId) params.set('order_id', orderId)
  if (ticketId) params.set('ticket_id', ticketId)
  if (category) params.set('category', category)
  const query = params.toString()

  return (
    <Button variant="outline" size="sm" asChild className={className}>
      <Link to={`${ROUTES.supportNew}${query ? `?${query}` : ''}`}>
        <LifeBuoy />
        {t('support.contact')}
      </Link>
    </Button>
  )
}

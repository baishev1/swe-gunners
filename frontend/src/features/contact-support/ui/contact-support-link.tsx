import { LifeBuoy } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import type { SupportCategory } from '@/entities/support'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'

interface ContactSupportLinkProps {
  eventId?: string
  category?: SupportCategory
  className?: string
}

export function ContactSupportLink({ eventId, category, className }: ContactSupportLinkProps) {
  const { t } = useTranslation()
  const params = new URLSearchParams()
  if (eventId) params.set('event_id', eventId)
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

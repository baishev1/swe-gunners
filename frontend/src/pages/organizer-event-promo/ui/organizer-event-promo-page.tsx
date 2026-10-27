import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { useEvent } from '@/entities/event'
import { PromoCampaignManager } from '@/features/manage-promo-campaigns'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'

export function OrganizerEventPromoPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const eventId = searchParams.get('event_id') ?? ''
  const event = useEvent(eventId)

  if (event.isPending) {
    return (
      <main className="mx-auto max-w-2xl p-6">
        <Skeleton className="h-64 w-full" />
      </main>
    )
  }

  if (event.isError) {
    return (
      <main className="mx-auto max-w-2xl p-6">
        <p className="text-destructive text-sm">{getErrorMessage(event.error)}</p>
      </main>
    )
  }

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">{t('promoCampaigns.title')}</h1>
        <p className="text-muted-foreground text-sm">{event.data.title}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button variant="link" asChild className="px-0">
          <Link to={`${ROUTES.organizerEventEdit}?event_id=${event.data.id}`}>
            {t('promoCampaigns.backToEvent')}
          </Link>
        </Button>
        <Button variant="link" asChild>
          <Link to={`${ROUTES.eventHistory}?event_id=${event.data.id}`}>{t('timeline.title')}</Link>
        </Button>
      </div>
      <PromoCampaignManager eventId={event.data.id} />
    </main>
  )
}

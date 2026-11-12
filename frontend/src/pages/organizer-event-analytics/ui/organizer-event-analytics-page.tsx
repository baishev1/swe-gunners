import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { useEvent } from '@/entities/event'
import { EventAnalyticsDashboard } from '@/features/event-analytics'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'

export function OrganizerEventAnalyticsPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const eventId = searchParams.get('event_id') ?? ''
  const event = useEvent(eventId)

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">{t('analytics.title')}</h1>
        {event.data && <p className="text-muted-foreground text-sm">{event.data.title}</p>}
      </div>
      <Button variant="link" asChild className="self-start px-0">
        <Link to={`${ROUTES.organizerEventEdit}?event_id=${eventId}`}>{t('analytics.back')}</Link>
      </Button>
      <EventAnalyticsDashboard eventId={eventId} />
    </main>
  )
}

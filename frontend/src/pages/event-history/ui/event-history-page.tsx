import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { useEvent } from '@/entities/event'
import { useMe } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { EventTimeline } from '@/widgets/event-timeline'

export function EventHistoryPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const eventId = searchParams.get('event_id') ?? ''
  const event = useEvent(eventId)
  const { data: me } = useMe()
  const backTo =
    me?.role === 'platform_admin'
      ? ROUTES.admin
      : `${ROUTES.organizerEventEdit}?event_id=${eventId}`

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">{t('timeline.title')}</h1>
        {event.data && <p className="text-muted-foreground text-sm">{event.data.title}</p>}
      </div>
      <Button variant="link" asChild className="self-start px-0">
        <Link to={backTo}>{t('timeline.back')}</Link>
      </Button>
      <EventTimeline eventId={eventId} />
    </main>
  )
}

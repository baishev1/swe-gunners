import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { type EventItem, type EventPhase, useOrganizerDashboard } from '@/entities/event'
import { DuplicateEventButton } from '@/features/duplicate-event'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDateTime } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'

const PHASES: EventPhase[] = ['upcoming', 'active', 'completed', 'cancelled']

function EventRow({ event }: { event: EventItem }) {
  const { t } = useTranslation()

  return (
    <li className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-4">
      <div className="flex min-w-0 flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate font-medium">{event.title}</span>
          <Badge variant={event.status === 'suspended' ? 'destructive' : 'outline'}>
            {t(`organizerDashboard.statuses.${event.status}`)}
          </Badge>
        </div>
        <span className="text-muted-foreground text-sm">
          {formatDateTime(event.start_time)} · {event.venue.name}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link to={`${ROUTES.organizerEventEdit}?event_id=${event.id}`}>
            {t('organizerDashboard.edit')}
          </Link>
        </Button>
        <Button variant="outline" size="sm" asChild>
          <Link to={`${ROUTES.eventHistory}?event_id=${event.id}`}>
            {t('organizerDashboard.history')}
          </Link>
        </Button>
        <DuplicateEventButton eventId={event.id} />
      </div>
    </li>
  )
}

export function OrganizerDashboardPage() {
  const { t } = useTranslation()
  const dashboard = useOrganizerDashboard()
  const defaultTab = PHASES.find((phase) => (dashboard.data?.[phase].length ?? 0) > 0)

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">{t('organizerDashboard.title')}</h1>
        <Button asChild>
          <Link to={ROUTES.organizerEventNew}>{t('organizerDashboard.newEvent')}</Link>
        </Button>
      </div>
      {dashboard.isPending && <Skeleton className="h-64 w-full" />}
      {dashboard.isError && <FieldError>{getErrorMessage(dashboard.error)}</FieldError>}
      {dashboard.data && (
        <Tabs defaultValue={defaultTab ?? 'upcoming'}>
          <TabsList>
            {PHASES.map((phase) => (
              <TabsTrigger key={phase} value={phase}>
                {t(`organizerDashboard.${phase}`)} ({dashboard.data[phase].length})
              </TabsTrigger>
            ))}
          </TabsList>
          {PHASES.map((phase) => (
            <TabsContent key={phase} value={phase}>
              {dashboard.data[phase].length === 0 ? (
                <p className="text-muted-foreground py-4 text-sm">
                  {t('organizerDashboard.empty')}
                </p>
              ) : (
                <ul className="flex flex-col gap-3 py-4">
                  {dashboard.data[phase].map((event) => (
                    <EventRow key={event.id} event={event} />
                  ))}
                </ul>
              )}
            </TabsContent>
          ))}
        </Tabs>
      )}
      <Link to={ROUTES.home} className="text-sm underline">
        {t('common.backToHome')}
      </Link>
    </main>
  )
}

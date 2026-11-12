import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { useEvent } from '@/entities/event'
import { EventStatusActions } from '@/features/change-event-status'
import { EventForm } from '@/features/event-form'
import { TicketTypeManager } from '@/features/manage-ticket-types'
import { PaidSalesChecklistCard } from '@/features/paid-sales-activation'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'

export function OrganizerEventEditPage() {
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
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">{event.data.title}</h1>
        <Badge variant="outline">{event.data.status}</Badge>
      </div>
      <EventStatusActions event={event.data} />
      <Button variant="link" asChild className="self-start">
        <Link to={`${ROUTES.eventDetail}?event_id=${event.data.id}`}>
          {t('organizerEventEdit.viewPage')}
        </Link>
      </Button>
      <Card>
        <CardHeader>
          <CardTitle>{t('organizerEventEdit.details')}</CardTitle>
        </CardHeader>
        <CardContent>
          <EventForm key={event.data.updated_at} event={event.data} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{t('organizerEventEdit.ticketTypes')}</CardTitle>
        </CardHeader>
        <CardContent>
          <TicketTypeManager eventId={event.data.id} />
        </CardContent>
      </Card>
      <PaidSalesChecklistCard eventId={event.data.id} />
    </main>
  )
}

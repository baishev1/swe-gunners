import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { useEvent } from '@/entities/event'
import { useMe } from '@/entities/session'
import { useTicketTypes } from '@/entities/ticket-type'
import { PromoLinkBanner } from '@/features/apply-promo-link'
import { ContactSupportLink } from '@/features/contact-support'
import { ReportEventForm } from '@/features/report-event'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDateTime, formatPrice } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardAction, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'

export function EventDetailPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const eventId = searchParams.get('event_id') ?? ''
  const access = searchParams.get('access')
  const event = useEvent(eventId, access)
  const ticketTypes = useTicketTypes(eventId, false, access)
  const me = useMe()

  if (event.isPending) {
    return (
      <main className="mx-auto max-w-3xl p-6">
        <Skeleton className="h-64 w-full" />
      </main>
    )
  }

  if (event.isError) {
    return (
      <main className="mx-auto max-w-3xl p-6">
        <p className="text-destructive text-sm">{getErrorMessage(event.error)}</p>
      </main>
    )
  }

  const data = event.data

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-6">
      {data.cover_image_url && (
        <img
          src={data.cover_image_url}
          alt={data.title}
          className="aspect-video w-full object-cover"
        />
      )}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{data.category}</Badge>
          {data.status === 'cancelled' && (
            <Badge variant="destructive">{t('eventDetail.cancelled')}</Badge>
          )}
        </div>
        <h1 className="text-3xl font-semibold">{data.title}</h1>
        <p className="text-muted-foreground text-sm">
          {formatDateTime(data.start_time)} – {formatDateTime(data.end_time)}
        </p>
        <p className="text-muted-foreground text-sm">
          {data.venue.name}, {data.venue.address}
        </p>
      </div>
      <PromoLinkBanner eventId={eventId} />
      {data.description && <p className="whitespace-pre-line">{data.description}</p>}
      <div className="flex flex-col gap-2">
        <h2 className="text-xl font-semibold">{t('eventDetail.refundPolicy')}</h2>
        <p className="text-muted-foreground text-sm whitespace-pre-line">
          {data.refund_policy?.trim() || t('eventDetail.defaultRefundPolicy')}
        </p>
      </div>
      <div className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold">{t('eventDetail.tickets')}</h2>
        {ticketTypes.data?.length === 0 && (
          <p className="text-muted-foreground text-sm">{t('eventDetail.noTickets')}</p>
        )}
        {ticketTypes.data?.map((ticketType) => (
          <Card key={ticketType.id}>
            <CardHeader>
              <CardTitle>{ticketType.name}</CardTitle>
              {ticketType.description && (
                <CardDescription>{ticketType.description}</CardDescription>
              )}
              <CardAction className="flex flex-col items-end gap-1">
                <span className="font-semibold">{formatPrice(ticketType.price)}</span>
                {ticketType.available > 0 ? (
                  <span className="text-muted-foreground text-xs">
                    {t('eventDetail.left', { count: ticketType.available })}
                  </span>
                ) : (
                  <Badge variant="destructive">{t('eventDetail.soldOut')}</Badge>
                )}
              </CardAction>
            </CardHeader>
          </Card>
        ))}
      </div>
      {data.status === 'published' &&
        ticketTypes.data?.some((ticketType) => ticketType.available > 0) && (
          <Button asChild>
            <Link
              to={`${ROUTES.checkout}?event_id=${data.id}${access ? `&access=${encodeURIComponent(access)}` : ''}`}
            >
              {t('eventDetail.getTickets')}
            </Link>
          </Button>
        )}
      <div className="flex flex-wrap gap-3">
        {me.data?.id === data.organizer_id && (
          <Button variant="outline" asChild>
            <Link to={`${ROUTES.organizerEventEdit}?event_id=${data.id}`}>
              {t('eventDetail.edit')}
            </Link>
          </Button>
        )}
        <ContactSupportLink eventId={data.id} category="event_information" />
        {me.data && me.data.id !== data.organizer_id && <ReportEventForm eventId={data.id} />}
      </div>
    </main>
  )
}

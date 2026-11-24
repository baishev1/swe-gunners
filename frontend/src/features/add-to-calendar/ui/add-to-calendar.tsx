import { CalendarPlus } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { type EventItem, useEvent } from '@/entities/event'
import { apiClient } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'

interface AddToCalendarProps {
  eventId: string
  access?: string | null
}

function compactUtc(value: string) {
  return new Date(value).toISOString().replace(/[-:]|\.\d{3}/g, '')
}

// Prefilled "new event" links; the attendee saves the entry themselves, so the platform
// never asks for access to their calendar account (SRS 4.11).
function googleLink(event: EventItem, location: string, details: string) {
  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: event.title,
    dates: `${compactUtc(event.start_time)}/${compactUtc(event.end_time)}`,
    ctz: event.timezone,
    location,
    details,
  })
  return `https://calendar.google.com/calendar/render?${params}`
}

function outlookLink(event: EventItem, location: string, details: string) {
  const params = new URLSearchParams({
    path: '/calendar/action/compose',
    rru: 'addevent',
    subject: event.title,
    startdt: new Date(event.start_time).toISOString(),
    enddt: new Date(event.end_time).toISOString(),
    location,
    body: details,
  })
  return `https://outlook.live.com/calendar/0/deeplink/compose?${params}`
}

export function AddToCalendar({ eventId, access }: AddToCalendarProps) {
  const { t } = useTranslation()
  const event = useEvent(eventId, access)

  if (!event.data) return null
  const data = event.data
  const location = `${data.venue.name}, ${data.venue.address}`
  const url = `${window.location.origin}${ROUTES.eventDetail}?event_id=${data.id}`
  const details = [data.description, url].filter(Boolean).join('\n\n')

  async function downloadIcs() {
    const response = await apiClient.get<Blob>('/events/calendar', {
      params: { event_id: eventId, access: access || undefined },
      responseType: 'blob',
    })
    const href = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = href
    link.download = `event-${eventId}.ics`
    link.click()
    URL.revokeObjectURL(href)
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button type="button" variant="outline" size="sm" onClick={downloadIcs}>
        <CalendarPlus />
        {data.status === 'cancelled' ? t('calendar.cancellationFile') : t('calendar.ics')}
      </Button>
      {data.status !== 'cancelled' && (
        <>
          <Button variant="outline" size="sm" asChild>
            <a href={googleLink(data, location, details)} target="_blank" rel="noreferrer">
              {t('calendar.google')}
            </a>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href={outlookLink(data, location, details)} target="_blank" rel="noreferrer">
              {t('calendar.outlook')}
            </a>
          </Button>
        </>
      )}
    </div>
  )
}

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

function GoogleCalendarIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect
        x="2"
        y="2"
        width="20"
        height="20"
        rx="3"
        fill="#fff"
        stroke="#4285F4"
        strokeWidth="2"
      />
      <path d="M2 17h5v5H5a3 3 0 0 1-3-3z" fill="#34A853" />
      <path d="M17 2h2a3 3 0 0 1 3 3v2h-5z" fill="#FBBC04" />
      <path d="M17 17h5l-5 5z" fill="#EA4335" />
      <text
        x="12"
        y="15.5"
        textAnchor="middle"
        fontSize="9"
        fontWeight="700"
        fontFamily="Arial, sans-serif"
        fill="#4285F4"
      >
        31
      </text>
    </svg>
  )
}

function OutlookIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="9" y="5" width="13" height="14" rx="2" fill="#28A8EA" />
      <path d="M14 8.5l4 3.5 4-3.5" fill="none" stroke="#fff" strokeWidth="1.5" />
      <rect x="2" y="3" width="12" height="18" rx="2" fill="#0078D4" />
      <circle cx="8" cy="12" r="3.5" fill="none" stroke="#fff" strokeWidth="2" />
    </svg>
  )
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
              <GoogleCalendarIcon />
              {t('calendar.google')}
            </a>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href={outlookLink(data, location, details)} target="_blank" rel="noreferrer">
              <OutlookIcon />
              {t('calendar.outlook')}
            </a>
          </Button>
        </>
      )}
    </div>
  )
}

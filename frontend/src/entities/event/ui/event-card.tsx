import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { ROUTES } from '@/shared/config'
import { formatDateTime } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Card, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'

import type { EventItem } from '../model/types'

export function EventCard({ event }: { event: EventItem }) {
  // formatDateTime reads the active language; subscribe so the card re-renders on change
  useTranslation()

  return (
    <Link to={`${ROUTES.eventDetail}?event_id=${event.id}`}>
      <Card className="h-full">
        <CardHeader>
          <Badge variant="secondary">{event.category}</Badge>
          <CardTitle>{event.title}</CardTitle>
          <CardDescription>
            {formatDateTime(event.start_time)} · {event.venue.name}
          </CardDescription>
        </CardHeader>
      </Card>
    </Link>
  )
}

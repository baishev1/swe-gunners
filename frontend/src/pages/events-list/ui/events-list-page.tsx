import { Link } from 'react-router-dom'

import { EventCard, useEvents } from '@/entities/event'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'

export function EventsListPage() {
  const events = useEvents()

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 p-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Events</h1>
        <Button asChild>
          <Link to={ROUTES.organizerEventNew}>Create event</Link>
        </Button>
      </div>
      {events.isPending && <Skeleton className="h-32 w-full" />}
      {events.isError && (
        <p className="text-destructive text-sm">{getErrorMessage(events.error)}</p>
      )}
      {events.data?.length === 0 && <p className="text-muted-foreground text-sm">No events yet.</p>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {events.data?.map((event) => (
          <EventCard key={event.id} event={event} />
        ))}
      </div>
    </main>
  )
}

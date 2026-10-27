import { useNavigate } from 'react-router-dom'

import { CreateVenueForm } from '@/features/create-venue'
import { EventForm } from '@/features/event-form'
import { ROUTES } from '@/shared/config'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'

export function OrganizerEventNewPage() {
  const navigate = useNavigate()

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <h1 className="text-2xl font-semibold">New event</h1>
      <Card>
        <CardHeader>
          <CardTitle>Event details</CardTitle>
        </CardHeader>
        <CardContent>
          <EventForm
            onSaved={(event) => navigate(`${ROUTES.organizerEventEdit}?event_id=${event.id}`)}
          />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Add a venue</CardTitle>
        </CardHeader>
        <CardContent>
          <CreateVenueForm />
        </CardContent>
      </Card>
    </main>
  )
}

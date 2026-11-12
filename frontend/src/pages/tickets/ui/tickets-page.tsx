import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { listTickets } from '@/shared/api'
import { Button } from '@/shared/ui'
import { TicketCard } from '@/entities/ticket'

export function TicketsPage() {
  const [searchParams] = useSearchParams()
  const orderId = searchParams.get('order_id') || undefined
  const eventId = searchParams.get('event_id') || undefined

  const {
    data: tickets = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['tickets', { orderId, eventId }],
    queryFn: () => listTickets({ order_id: orderId, event_id: eventId }),
  })

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Digital Tickets</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Present these QR codes at check-in or download them as PDF.
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/orders">My Orders</Link>
        </Button>
      </div>

      {isLoading && (
        <div className="text-center py-12 text-sm text-muted-foreground">
          Loading your tickets...
        </div>
      )}

      {error && (
        <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load tickets.
        </div>
      )}

      {!isLoading && !error && tickets.length === 0 && (
        <div className="text-center py-12 rounded-xl border border-dashed border-border p-8">
          <p className="text-muted-foreground text-sm">No tickets found.</p>
          <Button asChild className="mt-4" size="sm">
            <Link to="/events">Buy Tickets</Link>
          </Button>
        </div>
      )}

      <div className="grid gap-6">
        {tickets.map((ticket) => (
          <TicketCard key={ticket.id} ticket={ticket} />
        ))}
      </div>
    </div>
  )
}

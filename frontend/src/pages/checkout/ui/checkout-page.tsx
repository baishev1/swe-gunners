import { useSearchParams } from 'react-router-dom'
import { useTicketTypes } from '@/entities/ticket-type'
import { CheckoutForm } from '@/features/checkout'
import { Skeleton } from '@/shared/ui/skeleton'

export function CheckoutPage() {
  const [searchParams] = useSearchParams()
  const eventId = searchParams.get('event_id') ?? ''
  const ticketTypes = useTicketTypes(eventId)

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Checkout</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Complete your registration to receive your digital QR tickets.
        </p>
      </div>
      {ticketTypes.isPending ? (
        <Skeleton className="mx-auto h-64 max-w-xl" />
      ) : (
        <CheckoutForm
          eventId={eventId}
          ticketTypes={(ticketTypes.data ?? [])
            .filter((t) => t.available > 0)
            .map((t) => ({ id: t.id, name: t.name, price_kzt: t.price }))}
        />
      )}
    </div>
  )
}

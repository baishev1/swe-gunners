import { useSearchParams } from 'react-router-dom'
import { CheckoutForm, type CheckoutTicketTypeOption } from '@/features/checkout'

const DEFAULT_TICKET_TYPES: CheckoutTicketTypeOption[] = [
  { id: '11111111-1111-7111-8111-111111111111', name: 'Standard Admission', price_kzt: 5000 },
  { id: '22222222-2222-7222-8222-222222222222', name: 'VIP Pass', price_kzt: 15000 },
  { id: '33333333-3333-7333-8333-333333333333', name: 'Student Free Pass', price_kzt: 0 },
]

export function CheckoutPage() {
  const [searchParams] = useSearchParams()
  const eventId =
    searchParams.get('event_id') || '00000000-0000-7000-8000-000000000001'

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Checkout</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Complete your registration to receive your digital QR tickets.
        </p>
      </div>
      <CheckoutForm eventId={eventId} ticketTypes={DEFAULT_TICKET_TYPES} />
    </div>
  )
}

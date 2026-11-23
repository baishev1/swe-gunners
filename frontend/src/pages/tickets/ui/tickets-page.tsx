import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'
import { listTickets } from '@/shared/api'
import { Button } from '@/shared/ui'
import { TicketCard } from '@/entities/ticket'
import { ContactSupportLink } from '@/features/contact-support'

export function TicketsPage() {
  const { t } = useTranslation()
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
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            {t('tickets.title')}
          </h1>
          <p className="text-muted-foreground text-sm mt-1">{t('tickets.subtitle')}</p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/orders">{t('tickets.myOrders')}</Link>
        </Button>
      </div>

      {isLoading && (
        <div className="text-center py-12 text-sm text-muted-foreground">
          {t('tickets.loading')}
        </div>
      )}

      {error && (
        <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          {t('tickets.loadFailed')}
        </div>
      )}

      {!isLoading && !error && tickets.length === 0 && (
        <div className="text-center py-12 rounded-xl border border-dashed border-border p-8">
          <p className="text-muted-foreground text-sm">{t('tickets.empty')}</p>
          <Button asChild className="mt-4" size="sm">
            <Link to="/events">{t('tickets.buy')}</Link>
          </Button>
        </div>
      )}

      <div className="grid gap-6">
        {tickets.map((ticket) => (
          <div key={ticket.id} className="flex flex-col gap-2">
            <TicketCard ticket={ticket} />
            <div className="flex justify-end">
              <ContactSupportLink eventId={ticket.event_id} category="ticket_delivery" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

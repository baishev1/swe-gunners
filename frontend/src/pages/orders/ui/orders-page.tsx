import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { listOrders } from '@/shared/api'
import { Button } from '@/shared/ui'
import { OrderCard } from '@/entities/order'
import { ContactSupportLink } from '@/features/contact-support'

export function OrdersPage() {
  const { t } = useTranslation()
  const {
    data: orders = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['orders'],
    queryFn: () => listOrders(),
  })

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">{t('orders.title')}</h1>
          <p className="text-muted-foreground text-sm mt-1">{t('orders.subtitle')}</p>
        </div>
        <Button asChild size="sm">
          <Link to="/events">{t('orders.newOrder')}</Link>
        </Button>
      </div>

      {isLoading && (
        <div className="text-center py-12 text-sm text-muted-foreground">{t('orders.loading')}</div>
      )}

      {error && (
        <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          {t('orders.loadFailed')}
        </div>
      )}

      {!isLoading && !error && orders.length === 0 && (
        <div className="text-center py-12 rounded-xl border border-dashed border-border p-8">
          <p className="text-muted-foreground text-sm">{t('orders.empty')}</p>
          <Button asChild className="mt-4" size="sm">
            <Link to="/events">{t('orders.browse')}</Link>
          </Button>
        </div>
      )}

      <div className="space-y-4">
        {orders.map((order) => (
          <div key={order.id} className="flex flex-col gap-2">
            <OrderCard order={order} />
            <div className="flex justify-end">
              <ContactSupportLink eventId={order.event_id} category="payment" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

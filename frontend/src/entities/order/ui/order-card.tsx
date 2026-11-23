import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/shared/ui'
import { formatDateTime, formatPrice } from '@/shared/lib/format'
import type { Order } from '@/shared/types'
import { OrderStatusBadge } from './order-status-badge'

interface OrderCardProps {
  order: Order
}

export function OrderCard({ order }: OrderCardProps) {
  const { t } = useTranslation()

  return (
    <Card className="hover:border-foreground/20 transition-colors">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-base font-semibold">
            {t('orders.orderNumber', { number: order.id.slice(0, 8) })}
          </CardTitle>
          <p className="text-muted-foreground text-xs">{formatDateTime(order.created_at)}</p>
        </div>
        <OrderStatusBadge status={order.status} />
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="text-sm">
          <span className="text-muted-foreground">{t('orders.attendee')}: </span>
          <span className="font-medium">{order.customer_name}</span> ({order.customer_email})
        </div>
        <div className="text-xs text-muted-foreground">
          {order.items.map((item) => (
            <div key={item.id} className="flex justify-between py-0.5">
              <span>
                {item.quantity}x {item.ticket_type_name}
              </span>
              <span>{formatPrice(item.unit_price_kzt * item.quantity)}</span>
            </div>
          ))}
        </div>
        <div className="flex justify-between border-t pt-2 text-sm font-semibold">
          <span>{t('orders.total')}</span>
          <span>{formatPrice(order.total_amount_kzt)}</span>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end gap-2 border-t pt-3">
        {order.status === 'paid' && (
          <Link
            to={`/tickets?order_id=${order.id}`}
            className="text-xs font-semibold uppercase tracking-wider text-primary hover:underline"
          >
            {t('orders.viewTickets')}
          </Link>
        )}
      </CardFooter>
    </Card>
  )
}

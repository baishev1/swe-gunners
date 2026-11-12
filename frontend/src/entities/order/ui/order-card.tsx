import { Link } from 'react-router-dom'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/shared/ui'
import type { Order } from '@/shared/types'
import { OrderStatusBadge } from './order-status-badge'

interface OrderCardProps {
  order: Order
}

export function OrderCard({ order }: OrderCardProps) {
  const formattedDate = new Date(order.created_at).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })

  return (
    <Card className="hover:border-foreground/20 transition-colors">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-base font-semibold">Order #{order.id.slice(0, 8)}</CardTitle>
          <p className="text-muted-foreground text-xs">{formattedDate}</p>
        </div>
        <OrderStatusBadge status={order.status} />
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="text-sm">
          <span className="text-muted-foreground">Attendee: </span>
          <span className="font-medium">{order.customer_name}</span> ({order.customer_email})
        </div>
        <div className="text-xs text-muted-foreground">
          {order.items.map((item) => (
            <div key={item.id} className="flex justify-between py-0.5">
              <span>
                {item.quantity}x {item.ticket_type_name}
              </span>
              <span>{item.unit_price_kzt * item.quantity} ₸</span>
            </div>
          ))}
        </div>
        <div className="flex justify-between border-t pt-2 text-sm font-semibold">
          <span>Total:</span>
          <span>{order.total_amount_kzt} ₸</span>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end gap-2 border-t pt-3">
        {order.status === 'paid' && (
          <Link
            to={`/tickets?order_id=${order.id}`}
            className="text-xs font-semibold uppercase tracking-wider text-primary hover:underline"
          >
            View Tickets →
          </Link>
        )}
      </CardFooter>
    </Card>
  )
}

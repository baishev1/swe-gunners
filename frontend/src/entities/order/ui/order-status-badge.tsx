import { Badge } from '@/shared/ui'
import type { Order } from '@/shared/types'

interface OrderStatusBadgeProps {
  status: Order['status']
}

export function OrderStatusBadge({ status }: OrderStatusBadgeProps) {
  switch (status) {
    case 'paid':
      return <Badge variant="success">Paid</Badge>
    case 'pending':
      return <Badge variant="warning">Pending</Badge>
    case 'cancelled':
      return <Badge variant="destructive">Cancelled</Badge>
    case 'refunded':
      return <Badge variant="secondary">Refunded</Badge>
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}

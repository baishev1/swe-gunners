import { useTranslation } from 'react-i18next'
import { Badge } from '@/shared/ui'
import type { Order } from '@/shared/types'

interface OrderStatusBadgeProps {
  status: Order['status']
}

const VARIANTS = {
  paid: 'success',
  pending: 'warning',
  cancelled: 'destructive',
  refunded: 'secondary',
  expired: 'outline',
} as const

export function OrderStatusBadge({ status }: OrderStatusBadgeProps) {
  const { t } = useTranslation()
  return (
    <Badge variant={VARIANTS[status] ?? 'outline'}>
      {t(`organizerOrders.statuses.${status}`, { defaultValue: status })}
    </Badge>
  )
}

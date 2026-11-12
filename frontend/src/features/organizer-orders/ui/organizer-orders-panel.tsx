import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { getErrorMessage } from '@/shared/api'
import { formatDateTime, formatPrice } from '@/shared/lib/format'
import type { Order } from '@/shared/types'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'
import { Skeleton } from '@/shared/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'

import { useEventOrders, useRefundOrder } from '../api/organizer-orders-api'

function statusVariant(status: Order['status']) {
  if (status === 'paid') return 'success' as const
  if (status === 'pending') return 'warning' as const
  if (status === 'refunded') return 'secondary' as const
  if (status === 'cancelled') return 'destructive' as const
  return 'outline' as const
}

export function OrganizerOrdersPanel({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const orders = useEventOrders(eventId)
  const refundOrder = useRefundOrder(eventId)
  const [confirmingId, setConfirmingId] = useState<string | null>(null)

  if (orders.isPending) return <Skeleton className="h-32 w-full" />
  if (orders.isError) return <FieldError>{getErrorMessage(orders.error)}</FieldError>
  if (orders.data.length === 0) {
    return <p className="text-muted-foreground text-sm">{t('organizerOrders.empty')}</p>
  }

  return (
    <div className="flex flex-col gap-3">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t('organizerOrders.created')}</TableHead>
            <TableHead>{t('organizerOrders.customer')}</TableHead>
            <TableHead>{t('organizerOrders.items')}</TableHead>
            <TableHead className="text-right">{t('organizerOrders.total')}</TableHead>
            <TableHead>{t('organizerOrders.status')}</TableHead>
            <TableHead className="text-right">{t('organizerOrders.actions')}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.data.map((order) => (
            <TableRow key={order.id}>
              <TableCell className="whitespace-nowrap">
                {formatDateTime(order.created_at)}
              </TableCell>
              <TableCell>
                <div className="flex flex-col">
                  <span>{order.customer_name}</span>
                  <span className="text-muted-foreground text-xs">{order.customer_email}</span>
                </div>
              </TableCell>
              <TableCell>
                {order.items
                  .map((item) => `${item.ticket_type_name} × ${item.quantity}`)
                  .join(', ')}
              </TableCell>
              <TableCell className="text-right whitespace-nowrap">
                {formatPrice(order.total_amount_kzt)}
              </TableCell>
              <TableCell>
                <Badge variant={statusVariant(order.status)}>
                  {t(`organizerOrders.statuses.${order.status}`, { defaultValue: order.status })}
                </Badge>
              </TableCell>
              <TableCell>
                {order.status === 'paid' && (
                  <div className="flex justify-end gap-2">
                    {confirmingId === order.id ? (
                      <>
                        <Button
                          size="xs"
                          variant="destructive"
                          disabled={refundOrder.isPending}
                          onClick={() =>
                            refundOrder.mutate(order.id, {
                              onSuccess: () => setConfirmingId(null),
                            })
                          }
                        >
                          {t('organizerOrders.confirmRefund')}
                        </Button>
                        <Button
                          size="xs"
                          variant="ghost"
                          disabled={refundOrder.isPending}
                          onClick={() => setConfirmingId(null)}
                        >
                          {t('organizerOrders.cancel')}
                        </Button>
                      </>
                    ) : (
                      <Button size="xs" variant="outline" onClick={() => setConfirmingId(order.id)}>
                        {t('organizerOrders.refund')}
                      </Button>
                    )}
                  </div>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {refundOrder.isError && <FieldError>{getErrorMessage(refundOrder.error)}</FieldError>}
    </div>
  )
}

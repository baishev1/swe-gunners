import { type FormEvent, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { getErrorMessage } from '@/shared/api'
import { formatDateTime, formatPrice } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'

import { type AdminOrder, useAdminOrders } from '../api/admin-orders-api'

const STATUSES = ['pending', 'paid', 'cancelled', 'refunded', 'expired'] as const

export function AdminOrdersTable({ orders }: { orders: AdminOrder[] }) {
  const { t } = useTranslation()

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t('admin.ops.created')}</TableHead>
          <TableHead>{t('admin.ops.customer')}</TableHead>
          <TableHead>{t('admin.eventTitle')}</TableHead>
          <TableHead className="text-right">{t('admin.ops.amount')}</TableHead>
          <TableHead>{t('admin.status')}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {orders.map((order) => (
          <TableRow key={order.id}>
            <TableCell className="whitespace-nowrap">{formatDateTime(order.created_at)}</TableCell>
            <TableCell>
              <div className="flex flex-col">
                <span>{order.customer_name}</span>
                <span className="text-muted-foreground text-xs">{order.customer_email}</span>
              </div>
            </TableCell>
            <TableCell>{order.event_title ?? '—'}</TableCell>
            <TableCell className="text-right">{formatPrice(order.total_amount_kzt)}</TableCell>
            <TableCell>
              <Badge variant={order.status === 'paid' ? 'secondary' : 'outline'}>
                {t(`admin.ops.orderStatuses.${order.status}`, { defaultValue: order.status })}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export function AdminOrdersPanel() {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const orders = useAdminOrders(search, status)

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSearch(query.trim())
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSubmit} className="flex flex-wrap gap-2">
        <Input
          aria-label={t('admin.ops.searchOrders')}
          placeholder={t('admin.ops.searchOrders')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="max-w-xs"
        />
        <NativeSelect
          aria-label={t('admin.status')}
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <NativeSelectOption value="">{t('admin.allStatuses')}</NativeSelectOption>
          {STATUSES.map((value) => (
            <NativeSelectOption key={value} value={value}>
              {t(`admin.ops.orderStatuses.${value}`)}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <Button type="submit" variant="outline">
          {t('admin.search')}
        </Button>
      </form>
      {orders.isError && <FieldError>{getErrorMessage(orders.error)}</FieldError>}
      {orders.data && <AdminOrdersTable orders={orders.data} />}
      {orders.data?.length === 0 && (
        <p className="text-muted-foreground text-sm">{t('admin.nothingFound')}</p>
      )}
    </div>
  )
}

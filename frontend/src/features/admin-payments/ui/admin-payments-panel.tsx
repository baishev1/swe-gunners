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

import { type AdminPayment, useAdminPayments } from '../api/admin-payments-api'

const STATUSES = ['succeeded', 'failed'] as const

export function AdminPaymentsTable({ payments }: { payments: AdminPayment[] }) {
  const { t } = useTranslation()

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{t('admin.ops.created')}</TableHead>
          <TableHead>{t('admin.ops.transaction')}</TableHead>
          <TableHead>{t('admin.ops.customer')}</TableHead>
          <TableHead>{t('admin.eventTitle')}</TableHead>
          <TableHead className="text-right">{t('admin.ops.amount')}</TableHead>
          <TableHead>{t('admin.status')}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {payments.map((payment) => (
          <TableRow key={payment.id}>
            <TableCell className="whitespace-nowrap">
              {formatDateTime(payment.created_at)}
            </TableCell>
            <TableCell className="font-mono text-xs">{payment.transaction_id}</TableCell>
            <TableCell>{payment.customer_email ?? '—'}</TableCell>
            <TableCell>{payment.event_title ?? '—'}</TableCell>
            <TableCell className="text-right">{formatPrice(payment.amount_kzt)}</TableCell>
            <TableCell>
              <Badge variant={payment.status === 'failed' ? 'destructive' : 'secondary'}>
                {t(`admin.ops.paymentStatuses.${payment.status}`, {
                  defaultValue: payment.status,
                })}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export function AdminPaymentsPanel() {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const payments = useAdminPayments(search, status)

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSearch(query.trim())
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSubmit} className="flex flex-wrap gap-2">
        <Input
          aria-label={t('admin.ops.searchPayments')}
          placeholder={t('admin.ops.searchPayments')}
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
              {t(`admin.ops.paymentStatuses.${value}`)}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <Button type="submit" variant="outline">
          {t('admin.search')}
        </Button>
      </form>
      {payments.isError && <FieldError>{getErrorMessage(payments.error)}</FieldError>}
      {payments.data && <AdminPaymentsTable payments={payments.data} />}
      {payments.data?.length === 0 && (
        <p className="text-muted-foreground text-sm">{t('admin.nothingFound')}</p>
      )}
    </div>
  )
}

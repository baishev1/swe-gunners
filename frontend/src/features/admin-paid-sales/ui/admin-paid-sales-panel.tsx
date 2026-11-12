import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import type { PaidSalesActivation } from '@/entities/paid-sales'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDateTime, formatPrice } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'

import { useAdminPaidSales, useChangePaidSales } from '../api/admin-paid-sales-api'

const STATUSES = ['pending', 'active', 'suspended'] as const

function SuspendControl({ activation }: { activation: PaidSalesActivation }) {
  const { t } = useTranslation()
  const [reason, setReason] = useState('')
  const change = useChangePaidSales()

  if (activation.status === 'suspended') {
    return (
      <Button
        variant="outline"
        size="sm"
        disabled={change.isPending}
        onClick={() => change.mutate({ eventId: activation.event_id })}
      >
        {t('admin.paidSales.reinstate')}
      </Button>
    )
  }
  if (activation.status !== 'active') return null

  return (
    <form
      className="flex gap-2"
      onSubmit={(e) => {
        e.preventDefault()
        change.mutate({ eventId: activation.event_id, reason: reason.trim() })
      }}
    >
      <Input
        aria-label={t('admin.paidSales.reason')}
        placeholder={t('admin.paidSales.reason')}
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        className="h-8 w-44"
        required
      />
      <Button variant="destructive" size="sm" type="submit" disabled={change.isPending}>
        {t('admin.paidSales.suspend')}
      </Button>
      {change.isError && <FieldError>{getErrorMessage(change.error)}</FieldError>}
    </form>
  )
}

export function AdminPaidSalesPanel() {
  const { t } = useTranslation()
  const [status, setStatus] = useState('')
  const activations = useAdminPaidSales(status)

  return (
    <div className="flex flex-col gap-4">
      <NativeSelect
        aria-label={t('admin.status')}
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        className="self-start"
      >
        <NativeSelectOption value="">{t('admin.allStatuses')}</NativeSelectOption>
        {STATUSES.map((value) => (
          <NativeSelectOption key={value} value={value}>
            {t(`paidSales.statuses.${value}`)}
          </NativeSelectOption>
        ))}
      </NativeSelect>
      {activations.isError && <FieldError>{getErrorMessage(activations.error)}</FieldError>}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t('admin.eventTitle')}</TableHead>
            <TableHead>{t('admin.status')}</TableHead>
            <TableHead>{t('admin.paidSales.fee')}</TableHead>
            <TableHead>{t('admin.paidSales.activatedAt')}</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {activations.data?.map((activation) => (
            <TableRow key={activation.id}>
              <TableCell>
                <Link
                  className="underline-offset-4 hover:underline"
                  to={`${ROUTES.eventHistory}?event_id=${activation.event_id}`}
                >
                  {activation.event_title}
                </Link>
              </TableCell>
              <TableCell>
                <Badge variant={activation.status === 'suspended' ? 'destructive' : 'secondary'}>
                  {t(`paidSales.statuses.${activation.status}`)}
                </Badge>
                {activation.suspension_reason && (
                  <p className="text-muted-foreground mt-1 text-xs">
                    {activation.suspension_reason}
                  </p>
                )}
              </TableCell>
              <TableCell>
                {activation.fee_amount === null ? '—' : formatPrice(activation.fee_amount)}
              </TableCell>
              <TableCell>
                {activation.activated_at ? formatDateTime(activation.activated_at) : '—'}
              </TableCell>
              <TableCell className="flex justify-end">
                <SuspendControl activation={activation} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {activations.data?.length === 0 && (
        <p className="text-muted-foreground text-sm">{t('admin.nothingFound')}</p>
      )}
    </div>
  )
}

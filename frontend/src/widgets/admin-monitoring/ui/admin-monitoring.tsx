import { useTranslation } from 'react-i18next'

import { AdminOrdersTable } from '@/features/admin-orders'
import { AdminPaymentsTable } from '@/features/admin-payments'
import { getErrorMessage } from '@/shared/api'
import { formatPrice } from '@/shared/lib/format'
import { FieldError } from '@/shared/ui/field'
import { Skeleton } from '@/shared/ui/skeleton'

import { useAdminMonitoring } from '../api/admin-monitoring-api'

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-md border p-4">
      <span className="text-muted-foreground text-xs">{label}</span>
      <span className="text-xl font-semibold tabular-nums">{value}</span>
    </div>
  )
}

export function AdminMonitoring() {
  const { t } = useTranslation()
  const monitoring = useAdminMonitoring()
  const data = monitoring.data

  if (monitoring.isPending) return <Skeleton className="h-64 w-full" />
  if (monitoring.isError) return <FieldError>{getErrorMessage(monitoring.error)}</FieldError>
  if (!data) return null

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-3 sm:grid-cols-5">
        <Stat label={t('admin.ops.failedPayments')} value={String(data.failed_payments)} />
        <Stat label={t('admin.ops.refundedOrders')} value={String(data.refunded_orders)} />
        <Stat label={t('admin.ops.refundedAmount')} value={formatPrice(data.refunded_amount_kzt)} />
        <Stat label={t('admin.ops.cancelledOrders')} value={String(data.cancelled_orders)} />
        <Stat label={t('admin.ops.pendingOrders')} value={String(data.pending_orders)} />
      </div>
      <section className="flex flex-col gap-2">
        <h2 className="font-medium">{t('admin.ops.recentFailedPayments')}</h2>
        {data.recent_failed_payments.length === 0 ? (
          <p className="text-muted-foreground text-sm">{t('admin.nothingFound')}</p>
        ) : (
          <AdminPaymentsTable payments={data.recent_failed_payments} />
        )}
      </section>
      <section className="flex flex-col gap-2">
        <h2 className="font-medium">{t('admin.ops.recentRefunds')}</h2>
        {data.recent_refunds.length === 0 ? (
          <p className="text-muted-foreground text-sm">{t('admin.nothingFound')}</p>
        ) : (
          <AdminOrdersTable orders={data.recent_refunds} />
        )}
      </section>
    </div>
  )
}

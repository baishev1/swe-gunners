import { useTranslation } from 'react-i18next'
import { useState } from 'react'

import { type TimelineFilters, useEventTimeline } from '@/entities/audit-entry'
import { getErrorMessage } from '@/shared/api'
import { formatDateTime, fromDateTimeInput } from '@/shared/lib/format'
import { Field, FieldError, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Skeleton } from '@/shared/ui/skeleton'

const ACTIONS = [
  'event_published',
  'event_unpublished',
  'event_cancelled',
  'event_suspended',
  'event_duplicated',
  'event_created',
  'event_capacity_changed',
  'ticket_type_created',
  'ticket_price_changed',
  'ticket_capacity_changed',
  'promo_created',
  'promo_disabled',
  'ticket_checked_in',
  'ticket_check_in_reversed',
  'activation_fee_paid',
  'activation_fee_failed',
  'paid_terms_accepted',
  'paid_sales_activated',
  'paid_sales_suspended',
  'paid_sales_reinstated',
  'order_refunded',
  'order_cancelled',
  'order_expired',
  'staff_assigned',
  'staff_removed',
  'event_report_reviewed',
  'payment_succeeded',
  'payment_failed',
  'support_status_changed',
  'support_assigned',
] as const

export function EventTimeline({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const [action, setAction] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const filters: TimelineFilters = {
    action,
    dateFrom: fromDateTimeInput(dateFrom),
    dateTo: fromDateTimeInput(dateTo),
  }
  const timeline = useEventTimeline(eventId, filters)

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Field>
          <FieldLabel htmlFor="timeline-action">{t('timeline.action')}</FieldLabel>
          <NativeSelect
            id="timeline-action"
            value={action}
            onChange={(e) => setAction(e.target.value)}
          >
            <NativeSelectOption value="">{t('timeline.allActions')}</NativeSelectOption>
            {ACTIONS.map((value) => (
              <NativeSelectOption key={value} value={value}>
                {t(`timeline.actions.${value}`)}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="timeline-from">{t('timeline.from')}</FieldLabel>
          <Input
            id="timeline-from"
            type="datetime-local"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="timeline-to">{t('timeline.to')}</FieldLabel>
          <Input
            id="timeline-to"
            type="datetime-local"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </Field>
      </div>
      {timeline.isPending && <Skeleton className="h-32 w-full" />}
      {timeline.isError && <FieldError>{getErrorMessage(timeline.error)}</FieldError>}
      {timeline.data?.length === 0 && (
        <p className="text-muted-foreground text-sm">{t('timeline.empty')}</p>
      )}
      {timeline.data && timeline.data.length > 0 && (
        <ol className="border-border flex flex-col gap-4 border-l pl-4">
          {timeline.data.map((entry) => (
            <li key={entry.id} className="flex flex-col gap-1">
              <span className="text-muted-foreground text-xs">
                {formatDateTime(entry.created_at)}
                {entry.actor_name && ` · ${entry.actor_name}`}
              </span>
              <span className="text-sm font-medium">
                {t(`timeline.actions.${entry.action}`, { defaultValue: entry.action })}
              </span>
              <span className="text-sm">{entry.description}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}

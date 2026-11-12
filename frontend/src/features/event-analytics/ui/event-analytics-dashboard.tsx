import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { useTicketTypes } from '@/entities/ticket-type'
import { getErrorMessage } from '@/shared/api'
import { formatPrice } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Field, FieldError, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'

import { type EventAnalytics, useEventAnalytics } from '../api/event-analytics-api'

function startOfDay(value: string) {
  return value ? new Date(`${value}T00:00`).toISOString() : null
}

// The "to" date is inclusive in the UI, so the range ends at the next midnight.
function endOfDay(value: string) {
  if (!value) return null
  const date = new Date(`${value}T00:00`)
  date.setDate(date.getDate() + 1)
  return date.toISOString()
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-md border p-4">
      <span className="text-muted-foreground text-xs">{label}</span>
      <span className="text-xl font-semibold tabular-nums">{value}</span>
      {hint && <span className="text-muted-foreground text-xs">{hint}</span>}
    </div>
  )
}

function Meter({ percent }: { percent: number }) {
  return (
    <div className="bg-muted h-2 w-full overflow-hidden rounded-full">
      <div className="bg-primary h-full" style={{ width: `${Math.min(percent, 100)}%` }} />
    </div>
  )
}

function SalesChart({ points }: { points: EventAnalytics['sales_over_time'] }) {
  const { t, i18n } = useTranslation()
  if (points.length === 0) {
    return <p className="text-muted-foreground text-sm">{t('analytics.noSales')}</p>
  }
  const max = Math.max(...points.map((point) => point.tickets), 1)

  return (
    <div className="flex flex-col gap-2">
      <div className="flex h-40 items-end gap-1 overflow-x-auto" role="list">
        {points.map((point) => {
          const label = new Date(`${point.day}T00:00`).toLocaleDateString(i18n.language, {
            day: 'numeric',
            month: 'short',
          })
          return (
            <div
              key={point.day}
              role="listitem"
              className="flex min-w-8 flex-1 flex-col items-center justify-end gap-1"
              title={`${label}: ${t('analytics.ticketsCount', { count: point.tickets })}, ${formatPrice(point.gross_sales)}`}
            >
              <span className="text-xs tabular-nums">{point.tickets}</span>
              <div
                className="bg-primary w-full rounded-t-sm"
                style={{ height: `${(point.tickets / max) * 100}%`, minHeight: 2 }}
              />
              <span className="text-muted-foreground text-[10px] whitespace-nowrap">{label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function EventAnalyticsDashboard({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [ticketTypeId, setTicketTypeId] = useState('')
  const ticketTypes = useTicketTypes(eventId, true)
  const analytics = useEventAnalytics(eventId, {
    dateFrom: startOfDay(dateFrom),
    dateTo: endOfDay(dateTo),
    ticketTypeId,
  })
  const data = analytics.data

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <Field>
          <FieldLabel htmlFor="analytics-from">{t('analytics.from')}</FieldLabel>
          <Input
            id="analytics-from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="analytics-to">{t('analytics.to')}</FieldLabel>
          <Input
            id="analytics-to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="analytics-ticket-type">{t('analytics.ticketType')}</FieldLabel>
          <NativeSelect
            id="analytics-ticket-type"
            value={ticketTypeId}
            onChange={(e) => setTicketTypeId(e.target.value)}
          >
            <NativeSelectOption value="">{t('analytics.allTicketTypes')}</NativeSelectOption>
            {ticketTypes.data?.map((ticketType) => (
              <NativeSelectOption key={ticketType.id} value={ticketType.id}>
                {ticketType.name}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
      </div>

      {analytics.isPending && <Skeleton className="h-64 w-full" />}
      {analytics.isError && <FieldError>{getErrorMessage(analytics.error)}</FieldError>}

      {data && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>{t('analytics.capacity')}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="grid gap-3 sm:grid-cols-4">
                <Stat
                  label={t('analytics.totalCapacity')}
                  value={String(data.capacity.total_capacity)}
                />
                <Stat label={t('analytics.sold')} value={String(data.capacity.tickets_sold)} />
                <Stat
                  label={t('analytics.remaining')}
                  value={String(data.capacity.tickets_remaining)}
                />
                <Stat label={t('analytics.percentSold')} value={`${data.capacity.percent_sold}%`} />
              </div>
              <Meter percent={data.capacity.percent_sold} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('analytics.revenue')}</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-3">
              <Stat label={t('analytics.gross')} value={formatPrice(data.revenue.gross_sales)} />
              <Stat label={t('analytics.discounts')} value={formatPrice(data.revenue.discounts)} />
              <Stat label={t('analytics.refunds')} value={formatPrice(data.revenue.refunds)} />
              <Stat
                label={t('analytics.net')}
                value={formatPrice(data.revenue.net_revenue)}
                hint={t('analytics.netHint')}
              />
              <Stat
                label={t('analytics.processingFees')}
                value={formatPrice(data.revenue.processing_fees)}
              />
              <Stat
                label={t('analytics.estimatedPayout')}
                value={formatPrice(data.revenue.estimated_payout)}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('analytics.salesOverTime')}</CardTitle>
            </CardHeader>
            <CardContent>
              <SalesChart points={data.sales_over_time} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('analytics.byTicketType')}</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('analytics.ticketType')}</TableHead>
                    <TableHead className="text-right">{t('analytics.price')}</TableHead>
                    <TableHead className="text-right">{t('analytics.sold')}</TableHead>
                    <TableHead className="w-32">{t('analytics.percentSold')}</TableHead>
                    <TableHead className="text-right">{t('analytics.gross')}</TableHead>
                    <TableHead className="text-right">{t('analytics.checkedIn')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.ticket_types.map((row) => {
                    const percent = row.capacity ? (row.tickets_sold * 100) / row.capacity : 0
                    return (
                      <TableRow key={row.ticket_type_id}>
                        <TableCell>{row.name}</TableCell>
                        <TableCell className="text-right">{formatPrice(row.price)}</TableCell>
                        <TableCell className="text-right tabular-nums">
                          {row.tickets_sold}
                          {row.capacity > 0 && ` / ${row.capacity}`}
                        </TableCell>
                        <TableCell>
                          <Meter percent={percent} />
                        </TableCell>
                        <TableCell className="text-right">{formatPrice(row.gross_sales)}</TableCell>
                        <TableCell className="text-right tabular-nums">{row.checked_in}</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('analytics.campaigns')}</CardTitle>
            </CardHeader>
            <CardContent>
              {data.campaigns.length === 0 ? (
                <p className="text-muted-foreground text-sm">{t('analytics.noCampaigns')}</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('analytics.campaign')}</TableHead>
                      <TableHead className="text-right">{t('analytics.redemptions')}</TableHead>
                      <TableHead className="text-right">{t('analytics.tickets')}</TableHead>
                      <TableHead className="text-right">{t('analytics.discounts')}</TableHead>
                      <TableHead className="text-right">{t('analytics.net')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.campaigns.map((row) => (
                      <TableRow key={row.campaign_id}>
                        <TableCell className="flex items-center gap-2">
                          {row.name}
                          <span className="text-muted-foreground font-mono text-xs">
                            {row.code}
                          </span>
                          {row.is_disabled && (
                            <Badge variant="secondary">{t('analytics.disabled')}</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">{row.redemptions}</TableCell>
                        <TableCell className="text-right tabular-nums">{row.tickets}</TableCell>
                        <TableCell className="text-right">{formatPrice(row.discounts)}</TableCell>
                        <TableCell className="text-right">{formatPrice(row.revenue)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('analytics.attendance')}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <Stat label={t('analytics.checkedIn')} value={String(data.attendance.checked_in)} />
                <Stat label={t('analytics.absent')} value={String(data.attendance.absent)} />
                <Stat
                  label={t('analytics.percentCheckedIn')}
                  value={`${data.attendance.percent_checked_in}%`}
                />
              </div>
              <Meter percent={data.attendance.percent_checked_in} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

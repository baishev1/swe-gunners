import { type FormEvent, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui/button'
import { Field, FieldError, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'

import { type ReportKind, useExportReport } from '../api/admin-reports-api'

const REPORTS: ReportKind[] = ['orders', 'payments', 'events', 'users']

function startOfDay(value: string) {
  return value ? new Date(`${value}T00:00`).toISOString() : null
}

function endOfDay(value: string) {
  if (!value) return null
  const date = new Date(`${value}T00:00`)
  date.setDate(date.getDate() + 1)
  return date.toISOString()
}

export function AdminReportsPanel() {
  const { t } = useTranslation()
  const [report, setReport] = useState<ReportKind>('orders')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const exportReport = useExportReport()

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    exportReport.mutate({ report, dateFrom: startOfDay(dateFrom), dateTo: endOfDay(dateTo) })
  }

  return (
    <form onSubmit={handleSubmit} className="flex max-w-xl flex-col gap-4">
      <p className="text-muted-foreground text-sm">{t('admin.ops.reportsDescription')}</p>
      <div className="grid gap-4 sm:grid-cols-3">
        <Field>
          <FieldLabel htmlFor="report-kind">{t('admin.ops.report')}</FieldLabel>
          <NativeSelect
            id="report-kind"
            value={report}
            onChange={(e) => setReport(e.target.value as ReportKind)}
          >
            {REPORTS.map((value) => (
              <NativeSelectOption key={value} value={value}>
                {t(`admin.ops.reports.${value}`)}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="report-from">{t('admin.ops.from')}</FieldLabel>
          <Input
            id="report-from"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="report-to">{t('admin.ops.to')}</FieldLabel>
          <Input
            id="report-to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </Field>
      </div>
      {exportReport.isError && <FieldError>{getErrorMessage(exportReport.error)}</FieldError>}
      <Button type="submit" className="self-start" disabled={exportReport.isPending}>
        {t('admin.ops.download')}
      </Button>
    </form>
  )
}

import { Flag } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { type FormEvent, useState } from 'react'

import { getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui/button'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Textarea } from '@/shared/ui/textarea'

import { REPORT_CATEGORIES, type ReportCategory, useReportEvent } from '../api/report-event-api'

export function ReportEventForm({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [category, setCategory] = useState<ReportCategory>('fraud')
  const [reason, setReason] = useState('')
  const reportEvent = useReportEvent()

  if (reportEvent.isSuccess) {
    return <p className="text-muted-foreground text-sm">{t('reportEvent.sent')}</p>
  }

  if (!open) {
    return (
      <Button variant="ghost" size="sm" onClick={() => setOpen(true)}>
        <Flag />
        {t('reportEvent.open')}
      </Button>
    )
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    reportEvent.mutate({ eventId, category, reason })
  }

  return (
    <form onSubmit={handleSubmit} className="w-full rounded-md border p-4">
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="report-category">{t('reportEvent.category')}</FieldLabel>
          <NativeSelect
            id="report-category"
            className="w-full"
            value={category}
            onChange={(e) => setCategory(e.target.value as ReportCategory)}
          >
            {REPORT_CATEGORIES.map((value) => (
              <NativeSelectOption key={value} value={value}>
                {t(`reportEvent.categories.${value}`)}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="report-reason">{t('reportEvent.reason')}</FieldLabel>
          <Textarea
            id="report-reason"
            required
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </Field>
        {reportEvent.isError && <FieldError>{getErrorMessage(reportEvent.error)}</FieldError>}
        <div className="flex gap-2">
          <Button type="submit" disabled={reportEvent.isPending}>
            {t('reportEvent.submit')}
          </Button>
          <Button type="button" variant="outline" onClick={() => setOpen(false)}>
            {t('reportEvent.cancel')}
          </Button>
        </div>
      </FieldGroup>
    </form>
  )
}

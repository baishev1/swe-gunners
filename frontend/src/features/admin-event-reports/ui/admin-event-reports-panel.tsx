import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDateTime } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'

import {
  useEventReports,
  useReviewReport,
  useSuspendReportedEvent,
} from '../api/admin-event-reports-api'

export function AdminEventReportsPanel() {
  const { t } = useTranslation()
  const [status, setStatus] = useState('open')
  const reports = useEventReports(status)
  const reviewReport = useReviewReport()
  const suspendEvent = useSuspendReportedEvent()
  const error = reports.error ?? reviewReport.error ?? suspendEvent.error

  return (
    <div className="flex flex-col gap-4">
      <NativeSelect
        aria-label={t('admin.status')}
        value={status}
        onChange={(e) => setStatus(e.target.value)}
      >
        <NativeSelectOption value="open">{t('admin.eventReports.open')}</NativeSelectOption>
        <NativeSelectOption value="reviewed">{t('admin.eventReports.reviewed')}</NativeSelectOption>
        <NativeSelectOption value="">{t('admin.allStatuses')}</NativeSelectOption>
      </NativeSelect>
      {error && <FieldError>{getErrorMessage(error)}</FieldError>}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t('admin.eventTitle')}</TableHead>
            <TableHead>{t('admin.eventReports.category')}</TableHead>
            <TableHead>{t('admin.eventReports.reason')}</TableHead>
            <TableHead>{t('admin.eventReports.reporter')}</TableHead>
            <TableHead>{t('admin.eventReports.date')}</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {reports.data?.map((report) => (
            <TableRow key={report.id}>
              <TableCell>
                <Link
                  to={`${ROUTES.eventDetail}?event_id=${report.event.id}`}
                  className="underline-offset-4 hover:underline"
                >
                  {report.event.title}
                </Link>
                <div>
                  <Badge
                    variant={report.event.status === 'suspended' ? 'destructive' : 'secondary'}
                  >
                    {t(`admin.eventStatuses.${report.event.status}`, {
                      defaultValue: report.event.status,
                    })}
                  </Badge>
                </div>
              </TableCell>
              <TableCell>{t(`reportEvent.categories.${report.category}`)}</TableCell>
              <TableCell className="max-w-xs whitespace-pre-line">{report.reason}</TableCell>
              <TableCell>{report.reporter.email}</TableCell>
              <TableCell>{formatDateTime(report.created_at)}</TableCell>
              <TableCell className="flex justify-end gap-2">
                {report.event.status !== 'suspended' && report.event.status !== 'cancelled' && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={suspendEvent.isPending}
                    onClick={() => suspendEvent.mutate(report.event.id)}
                  >
                    {t('admin.suspendEvent')}
                  </Button>
                )}
                {report.status === 'open' && (
                  <Button
                    size="sm"
                    disabled={reviewReport.isPending}
                    onClick={() => reviewReport.mutate(report.id)}
                  >
                    {t('admin.eventReports.markReviewed')}
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {reports.data?.length === 0 && (
        <p className="text-muted-foreground text-sm">{t('admin.nothingFound')}</p>
      )}
    </div>
  )
}

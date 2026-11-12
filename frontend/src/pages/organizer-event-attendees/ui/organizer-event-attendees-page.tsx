import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'

import { useEvent } from '@/entities/event'
import { useEventAttendees } from '@/entities/event-attendee'
import type { TicketStatus } from '@/entities/event-attendee'
import { useTicketTypes } from '@/entities/ticket-type'
import { getErrorMessage } from '@/shared/api'
import { formatDateTime } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'

const TICKET_STATUSES: TicketStatus[] = ['valid', 'checked_in', 'cancelled', 'refunded']

export function OrganizerEventAttendeesPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const eventId = searchParams.get('event_id') ?? ''
  const event = useEvent(eventId)
  const attendees = useEventAttendees(eventId)
  const ticketTypes = useTicketTypes(eventId, true)
  const [ticketTypeFilter, setTicketTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const rows = useMemo(() => {
    const data = attendees.data ?? []
    return data.filter(
      (a) =>
        (!ticketTypeFilter || a.ticket_type_id === ticketTypeFilter) &&
        (!statusFilter || a.ticket_status === statusFilter),
    )
  }, [attendees.data, ticketTypeFilter, statusFilter])

  const checkedIn = (attendees.data ?? []).filter((a) => a.ticket_status === 'checked_in').length

  if (event.isPending || attendees.isPending) {
    return (
      <main className="mx-auto max-w-5xl p-6">
        <Skeleton className="h-96 w-full" />
      </main>
    )
  }

  if (event.isError || attendees.isError) {
    const error = event.error ?? attendees.error
    return (
      <main className="mx-auto max-w-5xl p-6">
        <p className="text-destructive text-sm">{getErrorMessage(error)}</p>
      </main>
    )
  }

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">
          {t('eventAttendees.title', { title: event.data.title })}
        </h1>
        <p className="text-muted-foreground text-sm">
          {t('eventAttendees.summary', {
            total: attendees.data?.length ?? 0,
            checkedIn,
          })}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <NativeSelect
          className="w-56"
          value={ticketTypeFilter}
          onChange={(e) => setTicketTypeFilter(e.target.value)}
          aria-label={t('eventAttendees.filterType')}
        >
          <NativeSelectOption value="">{t('eventAttendees.allTypes')}</NativeSelectOption>
          {ticketTypes.data?.map((tt) => (
            <NativeSelectOption key={tt.id} value={tt.id}>
              {tt.name}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <NativeSelect
          className="w-48"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label={t('eventAttendees.filterStatus')}
        >
          <NativeSelectOption value="">{t('eventAttendees.allStatuses')}</NativeSelectOption>
          {TICKET_STATUSES.map((status) => (
            <NativeSelectOption key={status} value={status}>
              {t(`eventAttendees.statuses.${status}`)}
            </NativeSelectOption>
          ))}
        </NativeSelect>
      </div>

      {rows.length === 0 ? (
        <p className="text-muted-foreground text-sm">{t('eventAttendees.empty')}</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t('eventAttendees.attendee')}</TableHead>
              <TableHead>{t('eventAttendees.ticketType')}</TableHead>
              <TableHead>{t('eventAttendees.status')}</TableHead>
              <TableHead>{t('eventAttendees.checkedInAt')}</TableHead>
              <TableHead>{t('eventAttendees.registeredAt')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((attendee) => (
              <TableRow key={attendee.ticket_id}>
                <TableCell>
                  <div className="flex flex-col">
                    <span className="font-medium">{attendee.attendee_name}</span>
                    <span className="text-muted-foreground text-xs">{attendee.attendee_email}</span>
                  </div>
                </TableCell>
                <TableCell>{attendee.ticket_type_name}</TableCell>
                <TableCell>
                  <Badge
                    variant={
                      attendee.ticket_status === 'checked_in'
                        ? 'default'
                        : attendee.ticket_status === 'valid'
                          ? 'secondary'
                          : 'outline'
                    }
                  >
                    {t(`eventAttendees.statuses.${attendee.ticket_status}`)}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {attendee.checked_in_at ? formatDateTime(attendee.checked_in_at) : '—'}
                </TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {formatDateTime(attendee.created_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </main>
  )
}

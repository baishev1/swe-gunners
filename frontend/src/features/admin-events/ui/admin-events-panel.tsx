import { useTranslation } from 'react-i18next'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'

import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDateTime } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'

import { useAdminEvents, useReinstateEvent, useSuspendEvent } from '../api/admin-events-api'

const STATUSES = ['draft', 'published', 'unpublished', 'cancelled', 'suspended'] as const

export function AdminEventsPanel() {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const events = useAdminEvents(search, status)
  const suspendEvent = useSuspendEvent()
  const reinstateEvent = useReinstateEvent()

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSearch(query.trim())
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSubmit} className="flex flex-wrap gap-2">
        <Input
          aria-label={t('admin.searchEvents')}
          placeholder={t('admin.searchEvents')}
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
              {t(`admin.eventStatuses.${value}`)}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <Button type="submit" variant="outline">
          {t('admin.search')}
        </Button>
      </form>
      {events.isError && <FieldError>{getErrorMessage(events.error)}</FieldError>}
      {suspendEvent.isError && <FieldError>{getErrorMessage(suspendEvent.error)}</FieldError>}
      {reinstateEvent.isError && <FieldError>{getErrorMessage(reinstateEvent.error)}</FieldError>}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t('admin.eventTitle')}</TableHead>
            <TableHead>{t('admin.startsAt')}</TableHead>
            <TableHead>{t('admin.status')}</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.data?.map((event) => (
            <TableRow key={event.id}>
              <TableCell>{event.title}</TableCell>
              <TableCell>{formatDateTime(event.start_time)}</TableCell>
              <TableCell>
                <Badge variant={event.status === 'suspended' ? 'destructive' : 'secondary'}>
                  {t(`admin.eventStatuses.${event.status}`, { defaultValue: event.status })}
                </Badge>
              </TableCell>
              <TableCell className="flex justify-end gap-2">
                <Button variant="link" size="sm" asChild>
                  <Link to={`${ROUTES.eventHistory}?event_id=${event.id}`}>
                    {t('admin.history')}
                  </Link>
                </Button>
                {event.status !== 'suspended' && event.status !== 'cancelled' && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={suspendEvent.isPending}
                    onClick={() => {
                      if (window.confirm(t('admin.confirmSuspendEvent', { title: event.title }))) {
                        suspendEvent.mutate(event.id)
                      }
                    }}
                  >
                    {t('admin.suspendEvent')}
                  </Button>
                )}
                {event.status === 'suspended' && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={reinstateEvent.isPending}
                    onClick={() => reinstateEvent.mutate(event.id)}
                  >
                    {t('admin.reinstateEvent')}
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {events.data?.length === 0 && (
        <p className="text-muted-foreground text-sm">{t('admin.nothingFound')}</p>
      )}
    </div>
  )
}

import { useTranslation } from 'react-i18next'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { type EventItem, eventKeys } from '@/entities/event'
import { apiClient, getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'

type StatusAction = 'publish' | 'unpublish' | 'cancel'

export function EventStatusActions({ event }: { event: EventItem }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const changeStatus = useMutation({
    mutationFn: async (action: StatusAction) =>
      (
        await apiClient.post<EventItem>(`/events/${action}`, null, {
          params: { event_id: event.id },
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: eventKeys.all }),
  })

  if (event.status === 'cancelled') return null

  return (
    <div className="flex flex-wrap items-center gap-2">
      {event.status === 'published' ? (
        <Button
          variant="outline"
          disabled={changeStatus.isPending}
          onClick={() => changeStatus.mutate('unpublish')}
        >
          {t('eventStatus.unpublish')}
        </Button>
      ) : (
        <Button disabled={changeStatus.isPending} onClick={() => changeStatus.mutate('publish')}>
          {t('eventStatus.publish')}
        </Button>
      )}
      <Button
        variant="destructive"
        disabled={changeStatus.isPending}
        onClick={() => changeStatus.mutate('cancel')}
      >
        {t('eventStatus.cancel')}
      </Button>
      {changeStatus.isError && <FieldError>{getErrorMessage(changeStatus.error)}</FieldError>}
    </div>
  )
}

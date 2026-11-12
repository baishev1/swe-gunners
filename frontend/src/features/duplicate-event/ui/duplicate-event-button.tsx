import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { type EventItem, eventKeys } from '@/entities/event'
import { apiClient, getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'

/** Copies the event's details into a new draft; orders, tickets and check-ins stay behind. */
export function DuplicateEventButton({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const duplicate = useMutation({
    mutationFn: async () =>
      (
        await apiClient.post<EventItem>('/events/duplicate', null, {
          params: { event_id: eventId },
        })
      ).data,
    onSuccess: async (copy) => {
      await queryClient.invalidateQueries({ queryKey: eventKeys.all })
      void navigate(`${ROUTES.organizerEventEdit}?event_id=${copy.id}`)
    },
  })

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        disabled={duplicate.isPending}
        onClick={() => duplicate.mutate()}
      >
        {t('organizerDashboard.duplicate')}
      </Button>
      {duplicate.isError && <FieldError>{getErrorMessage(duplicate.error)}</FieldError>}
    </>
  )
}

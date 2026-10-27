import { useMutation, useQueryClient } from '@tanstack/react-query'

import { type EventItem, type EventPayload, eventKeys } from '@/entities/event'
import { apiClient } from '@/shared/api'

export function useSaveEvent(eventId?: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: EventPayload) => {
      if (eventId) {
        return (
          await apiClient.patch<EventItem>('/events/update', payload, {
            params: { event_id: eventId },
          })
        ).data
      }
      return (await apiClient.post<EventItem>('/events', payload)).data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: eventKeys.all }),
  })
}

import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { EventAttendee } from '../model/types'

export const eventAttendeeKeys = {
  all: ['event-attendees'] as const,
  byEvent: (eventId: string) => [...eventAttendeeKeys.all, eventId] as const,
}

export function useEventAttendees(eventId: string) {
  return useQuery({
    queryKey: eventAttendeeKeys.byEvent(eventId),
    queryFn: async () =>
      (
        await apiClient.get<EventAttendee[]>('/tickets/event-attendees', {
          params: { event_id: eventId },
        })
      ).data,
    enabled: Boolean(eventId),
  })
}

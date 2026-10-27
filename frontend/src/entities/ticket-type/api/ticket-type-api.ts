import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { TicketType } from '../model/types'

export const ticketTypeKeys = {
  all: ['ticket-types'] as const,
  byEvent: (eventId: string, includeHidden: boolean) =>
    [...ticketTypeKeys.all, eventId, includeHidden] as const,
}

export function useTicketTypes(eventId: string, includeHidden = false) {
  return useQuery({
    queryKey: ticketTypeKeys.byEvent(eventId, includeHidden),
    queryFn: async () =>
      (
        await apiClient.get<TicketType[]>('/ticket-types', {
          params: { event_id: eventId, include_hidden: includeHidden },
        })
      ).data,
    enabled: Boolean(eventId),
  })
}

import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { SeatMap } from '../model/types'

export const seatMapKeys = {
  all: ['seat-map'] as const,
  byEvent: (eventId: string) => [...seatMapKeys.all, eventId] as const,
}

// Polls so seats other attendees hold or buy show up without a reload (SRS 4.3.1).
export function useSeatMap(eventId: string, access?: string | null, enabled = true) {
  return useQuery({
    queryKey: [...seatMapKeys.byEvent(eventId), access ?? ''],
    queryFn: async () =>
      (
        await apiClient.get<SeatMap>('/seating/map', {
          params: { event_id: eventId, access: access || undefined },
        })
      ).data,
    enabled: Boolean(eventId) && enabled,
    refetchInterval: 15_000,
  })
}

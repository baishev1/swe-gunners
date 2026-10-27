import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { EventItem } from '../model/types'

export const eventKeys = {
  all: ['events'] as const,
  list: () => [...eventKeys.all, 'list'] as const,
  detail: (eventId: string) => [...eventKeys.all, 'detail', eventId] as const,
}

export function useEvents() {
  return useQuery({
    queryKey: eventKeys.list(),
    queryFn: async () => (await apiClient.get<EventItem[]>('/events')).data,
  })
}

export function useEvent(eventId: string) {
  return useQuery({
    queryKey: eventKeys.detail(eventId),
    queryFn: async () =>
      (await apiClient.get<EventItem>('/events/detail', { params: { event_id: eventId } })).data,
    enabled: Boolean(eventId),
  })
}

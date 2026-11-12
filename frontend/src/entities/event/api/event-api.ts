import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { EventItem, OrganizerDashboard } from '../model/types'

export const eventKeys = {
  all: ['events'] as const,
  list: () => [...eventKeys.all, 'list'] as const,
  dashboard: () => [...eventKeys.all, 'dashboard'] as const,
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

export function useOrganizerDashboard() {
  return useQuery({
    queryKey: eventKeys.dashboard(),
    queryFn: async () => (await apiClient.get<OrganizerDashboard>('/events/dashboard')).data,
  })
}

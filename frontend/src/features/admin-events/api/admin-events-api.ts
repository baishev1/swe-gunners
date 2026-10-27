import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { eventKeys } from '@/entities/event'
import { apiClient } from '@/shared/api'

export interface AdminEvent {
  id: string
  title: string
  start_time: string
  status: string
  organizer_id: string
}

const adminEventKeys = {
  all: ['admin', 'events'] as const,
  search: (q: string, status: string) => [...adminEventKeys.all, q, status] as const,
}

export function useAdminEvents(q: string, status: string) {
  return useQuery({
    queryKey: adminEventKeys.search(q, status),
    queryFn: async () =>
      (
        await apiClient.get<AdminEvent[]>('/admin/events', {
          params: { q: q || undefined, status: status || undefined },
        })
      ).data,
  })
}

export function useSuspendEvent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (eventId: string) =>
      (
        await apiClient.post<AdminEvent>('/admin/events/suspend', null, {
          params: { event_id: eventId },
        })
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: adminEventKeys.all })
      void queryClient.invalidateQueries({ queryKey: eventKeys.all })
    },
  })
}

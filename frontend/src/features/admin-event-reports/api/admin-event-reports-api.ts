import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { eventKeys } from '@/entities/event'
import { apiClient } from '@/shared/api'

export interface EventReport {
  id: string
  category: string
  reason: string
  status: 'open' | 'reviewed'
  event: { id: string; title: string; status: string }
  reporter: { id: string; email: string }
  created_at: string
}

const reportKeys = {
  all: ['admin', 'event-reports'] as const,
  list: (status: string) => [...reportKeys.all, status] as const,
}

export function useEventReports(status: string) {
  return useQuery({
    queryKey: reportKeys.list(status),
    queryFn: async () =>
      (
        await apiClient.get<EventReport[]>('/admin/event-reports', {
          params: { status: status || undefined },
        })
      ).data,
  })
}

export function useReviewReport() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (reportId: string) =>
      (
        await apiClient.post<EventReport>('/admin/event-reports/review', null, {
          params: { report_id: reportId },
        })
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: reportKeys.all })
    },
  })
}

export function useSuspendReportedEvent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (eventId: string) =>
      (await apiClient.post('/admin/events/suspend', null, { params: { event_id: eventId } })).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: reportKeys.all })
      void queryClient.invalidateQueries({ queryKey: ['admin', 'events'] })
      void queryClient.invalidateQueries({ queryKey: eventKeys.all })
    },
  })
}

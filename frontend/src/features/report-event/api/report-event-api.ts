import { useMutation } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

export const REPORT_CATEGORIES = ['fraud', 'inappropriate', 'misleading', 'other'] as const

export type ReportCategory = (typeof REPORT_CATEGORIES)[number]

interface ReportEventPayload {
  eventId: string
  category: ReportCategory
  reason: string
}

export function useReportEvent() {
  return useMutation({
    mutationFn: async ({ eventId, category, reason }: ReportEventPayload) =>
      (
        await apiClient.post(
          '/event-reports',
          { category, reason },
          { params: { event_id: eventId } },
        )
      ).data,
  })
}

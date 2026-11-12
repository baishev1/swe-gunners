import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { PaidSalesChecklist } from '../model/types'

export const paidSalesKeys = {
  all: ['paid-sales'] as const,
  checklist: (eventId: string) => [...paidSalesKeys.all, 'checklist', eventId] as const,
}

export function usePaidSalesChecklist(eventId: string) {
  return useQuery({
    queryKey: paidSalesKeys.checklist(eventId),
    queryFn: async () =>
      (
        await apiClient.get<PaidSalesChecklist>('/paid-sales/checklist', {
          params: { event_id: eventId },
        })
      ).data,
    enabled: Boolean(eventId),
  })
}

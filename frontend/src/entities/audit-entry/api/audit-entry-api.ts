import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { AuditEntry, TimelineFilters } from '../model/types'

export const auditEntryKeys = {
  all: ['audit-log'] as const,
  timeline: (eventId: string, filters: TimelineFilters) =>
    [...auditEntryKeys.all, eventId, filters] as const,
}

export function useEventTimeline(eventId: string, filters: TimelineFilters) {
  return useQuery({
    queryKey: auditEntryKeys.timeline(eventId, filters),
    queryFn: async () =>
      (
        await apiClient.get<AuditEntry[]>('/audit-log/timeline', {
          params: {
            event_id: eventId,
            action: filters.action || undefined,
            date_from: filters.dateFrom ?? undefined,
            date_to: filters.dateTo ?? undefined,
          },
        })
      ).data,
    enabled: Boolean(eventId),
  })
}

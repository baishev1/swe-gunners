import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

export interface AnalyticsFilters {
  dateFrom: string | null
  dateTo: string | null
  ticketTypeId: string
}

export interface EventAnalytics {
  event_id: string
  capacity: {
    total_capacity: number
    tickets_sold: number
    tickets_remaining: number
    percent_sold: number
  }
  revenue: {
    gross_sales: number
    discounts: number
    refunds: number
    net_revenue: number
    processing_fees: number
    estimated_payout: number
  }
  sales_over_time: { day: string; orders: number; tickets: number; gross_sales: number }[]
  ticket_types: {
    ticket_type_id: string
    name: string
    price: number
    capacity: number
    tickets_sold: number
    gross_sales: number
    checked_in: number
  }[]
  campaigns: {
    campaign_id: string
    name: string
    code: string
    is_disabled: boolean
    redemptions: number
    tickets: number
    discounts: number
    revenue: number
  }[]
  attendance: { checked_in: number; absent: number; percent_checked_in: number }
}

const analyticsKeys = {
  all: ['analytics'] as const,
  event: (eventId: string, filters: AnalyticsFilters) =>
    [...analyticsKeys.all, eventId, filters] as const,
}

export function useEventAnalytics(eventId: string, filters: AnalyticsFilters) {
  return useQuery({
    queryKey: analyticsKeys.event(eventId, filters),
    queryFn: async () =>
      (
        await apiClient.get<EventAnalytics>('/analytics/event', {
          params: {
            event_id: eventId,
            date_from: filters.dateFrom ?? undefined,
            date_to: filters.dateTo ?? undefined,
            ticket_type_id: filters.ticketTypeId || undefined,
          },
        })
      ).data,
    enabled: Boolean(eventId),
  })
}

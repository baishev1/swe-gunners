import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { PromoCampaign } from '../model/types'

export const promoCampaignKeys = {
  all: ['promo-campaigns'] as const,
  byEvent: (eventId: string) => [...promoCampaignKeys.all, eventId] as const,
  qr: (campaignId: string) => [...promoCampaignKeys.all, 'qr', campaignId] as const,
}

export function usePromoCampaigns(eventId: string) {
  return useQuery({
    queryKey: promoCampaignKeys.byEvent(eventId),
    queryFn: async () =>
      (
        await apiClient.get<PromoCampaign[]>('/promo/campaigns', {
          params: { event_id: eventId },
        })
      ).data,
    enabled: Boolean(eventId),
  })
}

export function useCampaignQr(campaignId: string) {
  return useQuery({
    queryKey: promoCampaignKeys.qr(campaignId),
    queryFn: async () =>
      (
        await apiClient.get<string>('/promo/campaigns/qr', {
          params: { campaign_id: campaignId },
          responseType: 'text',
        })
      ).data,
  })
}

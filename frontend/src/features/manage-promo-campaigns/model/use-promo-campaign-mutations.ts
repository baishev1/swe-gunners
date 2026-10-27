import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  type PromoCampaign,
  type PromoCampaignPayload,
  promoCampaignKeys,
} from '@/entities/promo-campaign'
import { apiClient } from '@/shared/api'

export function useCreatePromoCampaign(eventId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: PromoCampaignPayload) =>
      (
        await apiClient.post<PromoCampaign>('/promo/campaigns', payload, {
          params: { event_id: eventId },
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: promoCampaignKeys.all }),
  })
}

export function useDisablePromoCampaign() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (campaignId: string) =>
      (
        await apiClient.post<PromoCampaign>('/promo/campaigns/disable', null, {
          params: { campaign_id: campaignId },
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: promoCampaignKeys.all }),
  })
}

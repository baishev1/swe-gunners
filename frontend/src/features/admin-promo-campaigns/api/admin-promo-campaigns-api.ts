import { useQuery } from '@tanstack/react-query'

import type { PromoCampaign } from '@/entities/promo-campaign'
import { apiClient } from '@/shared/api'

export function useAdminPromoCampaigns(q: string) {
  return useQuery({
    queryKey: ['admin', 'promo-campaigns', q],
    queryFn: async () =>
      (
        await apiClient.get<PromoCampaign[]>('/admin/promo-campaigns', {
          params: { q: q || undefined },
        })
      ).data,
  })
}

import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

export interface AdminOrder {
  id: string
  event_id: string
  event_title: string | null
  user_id: string | null
  customer_name: string
  customer_email: string
  total_amount_kzt: number
  status: string
  created_at: string
}

export function useAdminOrders(q: string, status: string) {
  return useQuery({
    queryKey: ['admin', 'orders', q, status],
    queryFn: async () =>
      (
        await apiClient.get<AdminOrder[]>('/admin/orders', {
          params: { q: q || undefined, status: status || undefined },
        })
      ).data,
  })
}

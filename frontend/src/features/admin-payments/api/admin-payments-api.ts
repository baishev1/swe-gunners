import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

export interface AdminPayment {
  id: string
  order_id: string
  amount_kzt: number
  status: string
  provider: string
  transaction_id: string
  customer_email: string | null
  event_title: string | null
  created_at: string
}

export function useAdminPayments(q: string, status: string) {
  return useQuery({
    queryKey: ['admin', 'payments', q, status],
    queryFn: async () =>
      (
        await apiClient.get<AdminPayment[]>('/admin/payments', {
          params: { q: q || undefined, status: status || undefined },
        })
      ).data,
  })
}

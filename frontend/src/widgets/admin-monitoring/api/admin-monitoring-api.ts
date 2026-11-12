import { useQuery } from '@tanstack/react-query'

import type { AdminOrder } from '@/features/admin-orders'
import type { AdminPayment } from '@/features/admin-payments'
import { apiClient } from '@/shared/api'

export interface AdminMonitoring {
  failed_payments: number
  refunded_orders: number
  refunded_amount_kzt: number
  cancelled_orders: number
  pending_orders: number
  recent_failed_payments: AdminPayment[]
  recent_refunds: AdminOrder[]
}

export function useAdminMonitoring() {
  return useQuery({
    queryKey: ['admin', 'monitoring'],
    queryFn: async () => (await apiClient.get<AdminMonitoring>('/admin/monitoring')).data,
  })
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { type PaidSalesActivation, paidSalesKeys } from '@/entities/paid-sales'
import { apiClient } from '@/shared/api'

const adminPaidSalesKeys = {
  all: ['admin', 'paid-sales'] as const,
  byStatus: (status: string) => [...adminPaidSalesKeys.all, status] as const,
}

export function useAdminPaidSales(status: string) {
  return useQuery({
    queryKey: adminPaidSalesKeys.byStatus(status),
    queryFn: async () =>
      (
        await apiClient.get<PaidSalesActivation[]>('/admin/paid-sales', {
          params: { status: status || undefined },
        })
      ).data,
  })
}

export function useChangePaidSales() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ eventId, reason }: { eventId: string; reason?: string }) =>
      (
        await apiClient.post<PaidSalesActivation>(
          reason === undefined ? '/admin/paid-sales/reinstate' : '/admin/paid-sales/suspend',
          reason === undefined ? null : { reason },
          { params: { event_id: eventId } },
        )
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: adminPaidSalesKeys.all })
      void queryClient.invalidateQueries({ queryKey: paidSalesKeys.all })
    },
  })
}

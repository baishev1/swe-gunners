import { useMutation, useQueryClient } from '@tanstack/react-query'

import { type PaidSalesChecklist, paidSalesKeys } from '@/entities/paid-sales'
import { apiClient } from '@/shared/api'

type ChecklistStep = 'pay-fee' | 'accept-terms' | 'activate'

export function usePaidSalesStep(eventId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (step: ChecklistStep) =>
      (
        await apiClient.post<PaidSalesChecklist>(
          `/paid-sales/${step}`,
          step === 'pay-fee' ? { simulate_failure: false } : null,
          { params: { event_id: eventId } },
        )
      ).data,
    onSuccess: (checklist) => queryClient.setQueryData(paidSalesKeys.checklist(eventId), checklist),
  })
}

export function useVerifyIdentity() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => (await apiClient.post('/organizers/verify-identity')).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: paidSalesKeys.all }),
  })
}

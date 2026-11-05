import { useMutation, useQueryClient } from '@tanstack/react-query'

import { type TicketType, type TicketTypePayload, ticketTypeKeys } from '@/entities/ticket-type'
import { paidSalesKeys } from '@/entities/paid-sales'
import { apiClient } from '@/shared/api'

export function useCreateTicketType(eventId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: TicketTypePayload) =>
      (
        await apiClient.post<TicketType>('/ticket-types', payload, {
          params: { event_id: eventId },
        })
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ticketTypeKeys.all })
      void queryClient.invalidateQueries({ queryKey: paidSalesKeys.all })
    },
  })
}

export function useUpdateTicketType() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...payload }: Partial<TicketTypePayload> & { id: string }) =>
      (
        await apiClient.patch<TicketType>('/ticket-types/update', payload, {
          params: { ticket_type_id: id },
        })
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ticketTypeKeys.all })
      void queryClient.invalidateQueries({ queryKey: paidSalesKeys.all })
    },
  })
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { ticketTypeKeys } from '@/entities/ticket-type'
import { apiClient } from '@/shared/api'
import type { Order } from '@/shared/types'

const organizerOrderKeys = {
  all: ['organizer', 'orders'] as const,
  byEvent: (eventId: string) => [...organizerOrderKeys.all, eventId] as const,
}

export function useEventOrders(eventId: string) {
  return useQuery({
    queryKey: organizerOrderKeys.byEvent(eventId),
    queryFn: async () =>
      (await apiClient.get<Order[]>('/orders/manage', { params: { event_id: eventId } })).data,
    enabled: Boolean(eventId),
  })
}

export function useRefundOrder(eventId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (orderId: string) =>
      (await apiClient.post<Order>('/orders/refund', null, { params: { order_id: orderId } })).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: organizerOrderKeys.byEvent(eventId) })
      void queryClient.invalidateQueries({ queryKey: ['analytics'] })
      void queryClient.invalidateQueries({ queryKey: ticketTypeKeys.all })
    },
  })
}

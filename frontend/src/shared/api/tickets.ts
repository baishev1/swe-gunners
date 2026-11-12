import { apiClient } from './client'
import type { Ticket } from '@/shared/types'

export async function listTickets(params?: {
  order_id?: string
  event_id?: string
}): Promise<Ticket[]> {
  const response = await apiClient.get<Ticket[]>('/tickets', { params })
  return response.data
}

export async function getTicketDetail(ticketId: string): Promise<Ticket> {
  const response = await apiClient.get<Ticket>('/tickets/detail', {
    params: { ticket_id: ticketId },
  })
  return response.data
}

export async function downloadTicketPdf(ticketId: string): Promise<Blob> {
  const response = await apiClient.get<Blob>('/tickets/pdf', {
    params: { ticket_id: ticketId },
    responseType: 'blob',
  })
  return response.data
}

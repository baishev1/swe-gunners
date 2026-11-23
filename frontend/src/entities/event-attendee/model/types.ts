export type TicketStatus = 'valid' | 'checked_in' | 'cancelled' | 'refunded'

export type OrderStatus = 'pending' | 'paid' | 'cancelled' | 'refunded' | 'expired'

export interface EventAttendee {
  ticket_id: string
  order_id: string
  attendee_name: string
  attendee_email: string
  ticket_type_id: string
  ticket_type_name: string
  ticket_status: TicketStatus
  order_status: OrderStatus
  checked_in_at: string | null
  created_at: string
}

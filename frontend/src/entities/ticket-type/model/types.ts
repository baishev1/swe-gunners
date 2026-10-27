export interface TicketTypePayload {
  name: string
  description: string | null
  price: number
  quantity: number
  max_per_order: number | null
  sales_start_time: string | null
  sales_end_time: string | null
  is_hidden: boolean
}

export interface TicketType extends TicketTypePayload {
  id: string
  event_id: string
  reserved_count: number
  sold_count: number
  available: number
}

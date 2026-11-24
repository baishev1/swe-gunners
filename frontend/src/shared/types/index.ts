export interface OrderItem {
  id: string
  order_id: string
  ticket_type_id: string
  ticket_type_name: string
  unit_price_kzt: number
  quantity: number
  created_at: string
  updated_at: string
}

export interface Order {
  id: string
  event_id: string
  user_id?: string | null
  customer_name: string
  customer_email: string
  total_amount_kzt: number
  status: 'pending' | 'paid' | 'cancelled' | 'refunded' | 'expired'
  hold_expires_at?: string | null
  discount_kzt?: number
  promo_campaign_id?: string | null
  created_at: string
  updated_at: string
  items: OrderItem[]
}

export interface OrderItemCreate {
  ticket_type_id: string
  quantity: number
}

export interface OrderCreatePayload {
  event_id: string
  customer_name: string
  customer_email: string
  items: OrderItemCreate[]
  promo_code?: string | null
  access_token?: string | null
}

export interface Ticket {
  id: string
  order_id: string
  order_item_id: string
  event_id: string
  ticket_type_id: string
  ticket_type_name: string
  attendee_name: string
  attendee_email: string
  qr_token: string
  status: 'valid' | 'checked_in' | 'cancelled' | 'refunded'
  checked_in_at?: string | null
  created_at: string
  updated_at: string
}

export interface PaymentSimulatePayload {
  order_id: string
  simulate_failure?: boolean
}

export interface Payment {
  id: string
  order_id: string
  amount_kzt: number
  status: 'succeeded' | 'failed' | 'refunded'
  provider: string
  transaction_id: string
  created_at: string
  updated_at: string
}

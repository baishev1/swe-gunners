export type SupportTarget = 'organizer' | 'platform'

export type SupportStatus = 'open' | 'in_progress' | 'waiting_for_customer' | 'resolved'

export type SupportCategory =
  | 'ticket_delivery'
  | 'payment'
  | 'refund'
  | 'seating'
  | 'event_information'
  | 'check_in'
  | 'account'
  | 'activation'
  | 'technical'

export const SUPPORT_CATEGORIES: SupportCategory[] = [
  'ticket_delivery',
  'payment',
  'refund',
  'seating',
  'event_information',
  'check_in',
  'account',
  'activation',
  'technical',
]

export interface SupportCase {
  id: string
  requester_id: string
  event_id: string | null
  order_id?: string | null
  ticket_id?: string | null
  order_status?: string | null
  order_total_kzt?: number | null
  ticket_type_name?: string | null
  ticket_status?: string | null
  assignee_id: string | null
  target: SupportTarget
  category: SupportCategory
  subject: string
  status: SupportStatus
  created_at: string
  updated_at: string
}

export interface SupportMessage {
  id: string
  case_id: string
  author_id: string
  body: string
  created_at: string
}

export interface SupportCaseCreate {
  target: SupportTarget
  event_id?: string | null
  order_id?: string | null
  ticket_id?: string | null
  category: SupportCategory
  subject: string
  message: string
}

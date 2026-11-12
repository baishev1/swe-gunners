export type PaidSalesStatus = 'pending' | 'active' | 'suspended'

export interface PaidSalesChecklist {
  event_id: string
  status: PaidSalesStatus
  fee_amount: number
  fee_transaction_id: string | null
  fee_paid_at: string | null
  terms_accepted_at: string | null
  activated_at: string | null
  suspended_at: string | null
  suspension_reason: string | null
  has_paid_ticket_type: boolean
  identity_verified: boolean
  payout_account_ready: boolean
  fee_paid: boolean
  terms_accepted: boolean
  can_activate: boolean
}

export interface PaidSalesActivation {
  id: string
  event_id: string
  event_title: string
  status: PaidSalesStatus
  fee_amount: number | null
  fee_transaction_id: string | null
  fee_paid_at: string | null
  terms_accepted_at: string | null
  activated_at: string | null
  suspended_at: string | null
  suspension_reason: string | null
  created_at: string
  updated_at: string
}

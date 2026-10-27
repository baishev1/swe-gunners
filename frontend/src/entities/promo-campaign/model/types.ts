export type DiscountType = 'percent' | 'fixed'

export interface PromoCampaignPayload {
  name: string
  discount_type: DiscountType
  discount_value: number
  start_time: string | null
  end_time: string | null
  max_redemptions: number | null
  ticket_type_ids: string[]
}

export interface PromoCampaign extends PromoCampaignPayload {
  id: string
  event_id: string
  code: string
  redemption_count: number
  is_disabled: boolean
  created_at: string
  updated_at: string
}

export interface ResolvedPromo {
  event_id: string
  code: string
  discount_type: DiscountType
  discount_value: number
  end_time: string | null
}

export type SeatStatus = 'available' | 'held' | 'sold' | 'unavailable'

export interface Seat {
  id: string
  number: number
  accessible: boolean
  status: SeatStatus
}

export interface SeatRow {
  label: string
  seats: Seat[]
}

export type SeatTier = 'balcony' | 'upper' | 'lower'

export interface SeatSection {
  key: string
  name: string
  tier: SeatTier
  /** 0 left, 1 centre, 2 right, as drawn on the hall plan. */
  column: number
  category: number
  rows: SeatRow[]
}

export interface SeatCategory {
  category: number
  name: string
  seat_count: number
  ticket_type_id: string | null
  ticket_type_name: string | null
  price: number | null
  max_per_order: number | null
}

export interface SeatMap {
  layout_key: string
  name: string
  stage: 'top' | 'bottom'
  hold_minutes: number
  categories: SeatCategory[]
  sections: SeatSection[]
}

/** A seat the attendee picked, with what checkout needs to price and send it. */
export interface SelectedSeat {
  id: string
  sectionKey: string
  row: string
  number: number
  ticketTypeId: string
  price: number
}

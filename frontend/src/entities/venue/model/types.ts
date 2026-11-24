export interface Venue {
  id: string
  name: string
  address: string
  /** Predefined seating layout, e.g. "main_hall"; null for general admission. */
  layout_key: string | null
}

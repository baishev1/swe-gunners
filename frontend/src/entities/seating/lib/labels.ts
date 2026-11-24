import type { TFunction } from 'i18next'

/** "Section E" for lettered blocks, "Balcony left" for the balcony ones. */
export function sectionLabel(t: TFunction, key: string) {
  return t(`seating.sections.${key}`, { defaultValue: t('seating.section', { key }) })
}

/** Parses a seat id like "BC-J-20" into its section, row and number. */
export function parseSeatId(id: string) {
  const [sectionKey, row, number] = id.split('-')
  return { sectionKey, row, number }
}

// Tickets store the section's display name; map the balcony names back to their keys.
const SECTION_KEYS: Record<string, string> = {
  'Balcony left': 'BL',
  'Balcony centre': 'BC',
  'Balcony right': 'BR',
}

/** "Section E · row A · seat 15" for a ticket's stored section, row and seat. */
export function ticketSeatLabel(t: TFunction, section: string, row: string, seat: string) {
  return t('seating.seatShort', {
    section: sectionLabel(t, SECTION_KEYS[section] ?? section),
    row,
    number: seat,
  })
}

export function seatLabel(t: TFunction, id: string) {
  const { sectionKey, row, number } = parseSeatId(id)
  return t('seating.seatShort', { section: sectionLabel(t, sectionKey), row, number })
}

import { ArrowLeft } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import {
  type Seat,
  type SeatCategory,
  type SeatMap,
  type SeatSection,
  type SeatTier,
  type SelectedSeat,
  sectionLabel,
} from '@/entities/seating'
import { formatPrice } from '@/shared/lib/format'
import { Button } from '@/shared/ui'

// Each state has its own colour and its own symbol, so nothing relies on colour alone.
type SeatLook = 'available' | 'accessible' | 'selected' | 'held' | 'sold' | 'unavailable'

const LOOK_CLASS: Record<SeatLook, string> = {
  available: 'border-primary/70 bg-background text-foreground hover:bg-primary/15',
  accessible:
    'border-sky-600 bg-sky-50 text-sky-800 hover:bg-sky-100 dark:bg-sky-950 dark:text-sky-200',
  selected: 'border-primary bg-primary text-primary-foreground',
  held: 'border-amber-500 bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200',
  sold: 'border-transparent bg-muted-foreground/35 text-foreground/70',
  unavailable: 'border-dashed border-muted-foreground/40 bg-muted text-muted-foreground',
}

const LOOK_SYMBOL: Partial<Record<SeatLook, string>> = {
  accessible: '♿',
  selected: '✓',
  held: '⏳',
  sold: '×',
  unavailable: '–',
}

const TIERS: SeatTier[] = ['balcony', 'upper', 'lower']

function seatLook(seat: Seat, selected: boolean): SeatLook {
  if (selected) return 'selected'
  if (seat.status !== 'available') return seat.status
  return seat.accessible ? 'accessible' : 'available'
}

interface SeatPickerProps {
  map: SeatMap
  selected: SelectedSeat[]
  onChange: (seats: SelectedSeat[]) => void
  disabled?: boolean
}

export function SeatPicker({ map, selected, onChange, disabled }: SeatPickerProps) {
  const { t } = useTranslation()
  const [openKey, setOpenKey] = useState<string | null>(null)
  const [limitMessage, setLimitMessage] = useState<string | null>(null)
  const categories = new Map(map.categories.map((c) => [c.category, c]))
  const selectedIds = new Set(selected.map((s) => s.id))
  const open = map.sections.find((s) => s.key === openKey) ?? null

  const toggleSeat = (section: SeatSection, row: string, seat: Seat) => {
    setLimitMessage(null)
    if (selectedIds.has(seat.id)) {
      onChange(selected.filter((s) => s.id !== seat.id))
      return
    }
    const category = categories.get(section.category)
    if (seat.status !== 'available' || !category?.ticket_type_id || category.price === null) return
    const inCategory = selected.filter((s) => s.ticketTypeId === category.ticket_type_id).length
    if (category.max_per_order && inCategory >= category.max_per_order) {
      setLimitMessage(t('seating.maxReached', { count: category.max_per_order }))
      return
    }
    onChange([
      ...selected,
      {
        id: seat.id,
        sectionKey: section.key,
        row,
        number: seat.number,
        ticketTypeId: category.ticket_type_id,
        price: category.price,
      },
    ])
  }

  const stage = (
    <div className="mx-auto w-2/3 rounded-md border bg-muted py-1.5 text-center text-xs font-semibold tracking-widest text-muted-foreground uppercase">
      {t('seating.stage')}
    </div>
  )

  return (
    <div className="space-y-4">
      <Legend />
      {open ? (
        <SectionView
          section={open}
          category={categories.get(open.category)}
          selectedIds={selectedIds}
          onBack={() => setOpenKey(null)}
          onToggle={toggleSeat}
          disabled={disabled}
          stage={map.stage === 'bottom' ? stage : null}
        />
      ) : (
        <div className="space-y-3">
          {map.stage === 'top' && stage}
          {TIERS.map((tier) => (
            <div key={tier} className="space-y-1">
              <p className="text-muted-foreground text-xs font-medium">
                {t(`seating.tiers.${tier}`)}
              </p>
              <div className="grid grid-cols-3 gap-2">
                {map.sections
                  .filter((s) => s.tier === tier)
                  .sort((a, b) => a.column - b.column)
                  .map((section) => (
                    <SectionTile
                      key={section.key}
                      section={section}
                      category={categories.get(section.category)}
                      selectedIds={selectedIds}
                      onOpen={() => setOpenKey(section.key)}
                    />
                  ))}
              </div>
            </div>
          ))}
          {map.stage === 'bottom' && stage}
        </div>
      )}
      {limitMessage && (
        <p role="status" className="text-destructive text-xs">
          {limitMessage}
        </p>
      )}
    </div>
  )
}

function Legend() {
  const { t } = useTranslation()
  const looks: SeatLook[] = ['available', 'accessible', 'selected', 'held', 'sold', 'unavailable']
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs" aria-label={t('seating.legend')}>
      {looks.map((look) => (
        <li key={look} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className={`flex size-5 items-center justify-center rounded-sm border text-[10px] ${LOOK_CLASS[look]}`}
          >
            {LOOK_SYMBOL[look] ?? ''}
          </span>
          {t(`seating.status.${look}`)}
        </li>
      ))}
    </ul>
  )
}

interface SectionTileProps {
  section: SeatSection
  category: SeatCategory | undefined
  selectedIds: Set<string>
  onOpen: () => void
}

function SectionTile({ section, category, selectedIds, onOpen }: SectionTileProps) {
  const { t } = useTranslation()
  const seats = section.rows.flatMap((r) => r.seats)
  const free = seats.filter((s) => s.status === 'available').length
  const mine = seats.filter((s) => selectedIds.has(s.id)).length
  const name = sectionLabel(t, section.key)
  const price = category?.price != null ? formatPrice(category.price) : t('seating.notPriced')

  return (
    <button
      type="button"
      onClick={onOpen}
      aria-label={t('seating.openSection', { name, count: free, price })}
      className="flex min-w-0 flex-col items-center gap-1.5 rounded-md border p-2 text-center transition-colors hover:border-primary hover:bg-primary/5 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
    >
      {/* A miniature of the block; the button's label carries the information. */}
      <span aria-hidden className="flex w-full flex-col items-center gap-px overflow-hidden">
        {section.rows.map((row) => (
          <span key={row.label} className="flex gap-px">
            {[...row.seats].reverse().map((seat) => (
              <span
                key={seat.id}
                className={`size-[3px] sm:size-1.5 ${
                  selectedIds.has(seat.id)
                    ? 'bg-primary'
                    : seat.status === 'available'
                      ? 'bg-primary/35'
                      : seat.status === 'held'
                        ? 'bg-amber-500'
                        : 'bg-muted-foreground/40'
                }`}
              />
            ))}
          </span>
        ))}
      </span>
      <span className="text-xs leading-tight font-semibold break-words">{name}</span>
      <span className="text-muted-foreground text-[11px] leading-tight">
        {price}
        <br />
        {t('seating.seatsLeft', { count: free })}
        {mine > 0 && (
          <>
            <br />
            <span className="text-primary font-medium">
              {t('seating.selectedHere', { count: mine })}
            </span>
          </>
        )}
      </span>
    </button>
  )
}

interface SectionViewProps {
  section: SeatSection
  category: SeatCategory | undefined
  selectedIds: Set<string>
  onBack: () => void
  onToggle: (section: SeatSection, row: string, seat: Seat) => void
  disabled?: boolean
  stage: React.ReactNode
}

function SectionView({
  section,
  category,
  selectedIds,
  onBack,
  onToggle,
  disabled,
  stage,
}: SectionViewProps) {
  const { t } = useTranslation()
  const name = sectionLabel(t, section.key)
  const price = category?.price != null ? formatPrice(category.price) : t('seating.notPriced')

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Button type="button" variant="outline" size="sm" onClick={onBack}>
          <ArrowLeft className="mr-1 size-3.5" />
          {t('seating.backToHall')}
        </Button>
        <p className="text-sm">
          <span className="font-semibold">{name}</span>
          <span className="text-muted-foreground">
            {' · '}
            {category?.ticket_type_name ?? category?.name} · {price}
          </span>
        </p>
      </div>
      <div className="overflow-x-auto pb-1">
        <div className="mx-auto w-max space-y-1">
          {section.rows.map((row) => (
            <div key={row.label} className="flex items-center gap-1">
              <span className="text-muted-foreground w-5 shrink-0 text-center text-xs font-semibold">
                {row.label}
              </span>
              {/* Seats are numbered right to left, as on the hall plan. */}
              <div className="flex flex-1 justify-center gap-1">
                {[...row.seats].reverse().map((seat) => {
                  const isSelected = selectedIds.has(seat.id)
                  const look = seatLook(seat, isSelected)
                  const canToggle = isSelected || seat.status === 'available'
                  return (
                    <button
                      key={seat.id}
                      type="button"
                      disabled={disabled || !canToggle || category?.price == null}
                      aria-pressed={isSelected}
                      aria-label={t('seating.seatLabel', {
                        section: name,
                        row: row.label,
                        number: seat.number,
                        status: t(`seating.status.${look}`),
                      })}
                      title={`${t('seating.rowSeat', { row: row.label, number: seat.number })} · ${t(`seating.status.${look}`)}`}
                      onClick={() => onToggle(section, row.label, seat)}
                      className={`flex size-6 shrink-0 items-center sm:size-7 justify-center rounded-sm border text-[10px] font-medium tabular-nums transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none disabled:cursor-not-allowed ${LOOK_CLASS[look]}`}
                    >
                      {LOOK_SYMBOL[look] ?? seat.number}
                    </button>
                  )
                })}
              </div>
              <span className="text-muted-foreground w-5 shrink-0 text-center text-xs font-semibold">
                {row.label}
              </span>
            </div>
          ))}
        </div>
      </div>
      {stage}
    </div>
  )
}

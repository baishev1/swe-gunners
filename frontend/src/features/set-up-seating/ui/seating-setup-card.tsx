import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { eventKeys } from '@/entities/event'
import { paidSalesKeys } from '@/entities/paid-sales'
import { type SeatCategory, seatMapKeys, useSeatMap } from '@/entities/seating'
import { ticketTypeKeys } from '@/entities/ticket-type'
import { apiClient, getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { Skeleton } from '@/shared/ui/skeleton'

interface Draft {
  name: string
  price: string
}

/** Prices the venue layout's categories; each becomes one ticket type (SRS 4.3.1). */
export function SeatingSetupCard({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const seatMap = useSeatMap(eventId)

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('seatingSetup.title')}</CardTitle>
        {seatMap.data && (
          <p className="text-muted-foreground text-sm">
            {t('seatingSetup.description', {
              layout: seatMap.data.name,
              count: seatMap.data.categories.reduce((sum, c) => sum + c.seat_count, 0),
            })}
          </p>
        )}
      </CardHeader>
      <CardContent>
        {seatMap.isPending ? (
          <Skeleton className="h-40 w-full" />
        ) : seatMap.isError ? (
          <p className="text-destructive text-sm">{getErrorMessage(seatMap.error)}</p>
        ) : (
          <SeatingSetupForm eventId={eventId} categories={seatMap.data.categories} />
        )}
      </CardContent>
    </Card>
  )
}

function SeatingSetupForm({
  eventId,
  categories,
}: {
  eventId: string
  categories: SeatCategory[]
}) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [drafts, setDrafts] = useState<Record<number, Draft>>(() =>
    Object.fromEntries(
      categories.map((c) => [
        c.category,
        {
          name: c.ticket_type_name ?? t(`seatingSetup.categories.${c.category}`, c.name),
          price: c.price != null ? String(c.price / 100) : '',
        },
      ]),
    ),
  )
  const save = useMutation({
    mutationFn: async () =>
      (
        await apiClient.post(
          '/seating/setup',
          {
            categories: categories.map((c) => ({
              category: c.category,
              name: drafts[c.category].name,
              price: Math.round(Number(drafts[c.category].price) * 100),
            })),
          },
          { params: { event_id: eventId } },
        )
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ticketTypeKeys.all })
      void queryClient.invalidateQueries({ queryKey: seatMapKeys.all })
      void queryClient.invalidateQueries({ queryKey: paidSalesKeys.all })
      void queryClient.invalidateQueries({ queryKey: eventKeys.detail(eventId) })
    },
  })

  const update = (category: number, patch: Partial<Draft>) =>
    setDrafts((prev) => ({ ...prev, [category]: { ...prev[category], ...patch } }))

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    save.mutate()
  }

  return (
    <form onSubmit={handleSubmit}>
      <FieldGroup>
        {categories.map((c) => (
          <div key={c.category} className="grid gap-3 sm:grid-cols-[1fr_10rem]">
            <Field>
              <FieldLabel htmlFor={`seat-category-${c.category}`}>
                {t('seatingSetup.categoryLabel', { number: c.category, count: c.seat_count })}
              </FieldLabel>
              <Input
                id={`seat-category-${c.category}`}
                required
                value={drafts[c.category].name}
                onChange={(e) => update(c.category, { name: e.target.value })}
              />
            </Field>
            <Field>
              <FieldLabel htmlFor={`seat-price-${c.category}`}>{t('ticketTypes.price')}</FieldLabel>
              <Input
                id={`seat-price-${c.category}`}
                type="number"
                min={0}
                step="0.01"
                required
                value={drafts[c.category].price}
                onChange={(e) => update(c.category, { price: e.target.value })}
              />
            </Field>
          </div>
        ))}
        {save.isError && <FieldError>{getErrorMessage(save.error)}</FieldError>}
        {save.isSuccess && (
          <p role="status" className="text-sm text-emerald-700 dark:text-emerald-400">
            {t('seatingSetup.saved')}
          </p>
        )}
        <Button type="submit" disabled={save.isPending}>
          {t('seatingSetup.save')}
        </Button>
      </FieldGroup>
    </form>
  )
}

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { type FormEvent, useState } from 'react'

import { type Venue, venueKeys } from '@/entities/venue'
import { apiClient, getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui/button'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'

// The predefined layouts the backend knows; there is no layout editor (SRS 4.3.1).
const LAYOUTS = ['main_hall'] as const

export function CreateVenueForm() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [address, setAddress] = useState('')
  const [layout, setLayout] = useState('')
  const createVenue = useMutation({
    mutationFn: async () =>
      (await apiClient.post<Venue>('/venues', { name, address, layout_key: layout || null })).data,
    onSuccess: () => {
      setName('')
      setAddress('')
      setLayout('')
      return queryClient.invalidateQueries({ queryKey: venueKeys.all })
    },
  })

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    createVenue.mutate()
  }

  return (
    <form onSubmit={handleSubmit}>
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="venue-name">{t('createVenue.name')}</FieldLabel>
          <Input id="venue-name" required value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field>
          <FieldLabel htmlFor="venue-address">{t('createVenue.address')}</FieldLabel>
          <Input
            id="venue-address"
            required
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="venue-layout">{t('createVenue.layout')}</FieldLabel>
          <NativeSelect
            id="venue-layout"
            className="w-full"
            value={layout}
            onChange={(e) => setLayout(e.target.value)}
          >
            <NativeSelectOption value="">{t('createVenue.layoutNone')}</NativeSelectOption>
            {LAYOUTS.map((key) => (
              <NativeSelectOption key={key} value={key}>
                {t(`createVenue.layouts.${key}`)}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
        {createVenue.isError && <FieldError>{getErrorMessage(createVenue.error)}</FieldError>}
        <Button type="submit" variant="outline" disabled={createVenue.isPending}>
          {t('createVenue.submit')}
        </Button>
      </FieldGroup>
    </form>
  )
}

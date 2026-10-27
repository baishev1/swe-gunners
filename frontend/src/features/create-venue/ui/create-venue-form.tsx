import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'

import { type Venue, venueKeys } from '@/entities/venue'
import { apiClient, getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui/button'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'

export function CreateVenueForm() {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [address, setAddress] = useState('')
  const createVenue = useMutation({
    mutationFn: async () => (await apiClient.post<Venue>('/venues', { name, address })).data,
    onSuccess: () => {
      setName('')
      setAddress('')
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
          <FieldLabel htmlFor="venue-name">Venue name</FieldLabel>
          <Input id="venue-name" required value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field>
          <FieldLabel htmlFor="venue-address">Address</FieldLabel>
          <Input
            id="venue-address"
            required
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
        </Field>
        {createVenue.isError && <FieldError>{getErrorMessage(createVenue.error)}</FieldError>}
        <Button type="submit" variant="outline" disabled={createVenue.isPending}>
          Add venue
        </Button>
      </FieldGroup>
    </form>
  )
}

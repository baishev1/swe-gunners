import { type FormEvent, useState } from 'react'

import { getErrorMessage } from '@/shared/api'
import { fromDateTimeInput } from '@/shared/lib/format'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'

import { useCreateTicketType } from '../model/use-ticket-type-mutations'

export function TicketTypeForm({ eventId }: { eventId: string }) {
  const createTicketType = useCreateTicketType(eventId)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [price, setPrice] = useState('0')
  const [quantity, setQuantity] = useState('')
  const [maxPerOrder, setMaxPerOrder] = useState('')
  const [salesStart, setSalesStart] = useState('')
  const [salesEnd, setSalesEnd] = useState('')
  const [isHidden, setIsHidden] = useState(false)

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    createTicketType.mutate(
      {
        name,
        description: description || null,
        price: Math.round(Number(price) * 100),
        quantity: Number(quantity),
        max_per_order: maxPerOrder ? Number(maxPerOrder) : null,
        sales_start_time: fromDateTimeInput(salesStart),
        sales_end_time: fromDateTimeInput(salesEnd),
        is_hidden: isHidden,
      },
      {
        onSuccess: () => {
          setName('')
          setDescription('')
          setPrice('0')
          setQuantity('')
          setMaxPerOrder('')
          setSalesStart('')
          setSalesEnd('')
          setIsHidden(false)
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit}>
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="ticket-name">Name</FieldLabel>
          <Input id="ticket-name" required value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field>
          <FieldLabel htmlFor="ticket-description">Description</FieldLabel>
          <Textarea
            id="ticket-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="ticket-price">Price, KZT (0 for free)</FieldLabel>
          <Input
            id="ticket-price"
            type="number"
            min={0}
            step="0.01"
            required
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="ticket-quantity">Quantity</FieldLabel>
          <Input
            id="ticket-quantity"
            type="number"
            min={1}
            required
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="ticket-max-per-order">Max per order</FieldLabel>
          <Input
            id="ticket-max-per-order"
            type="number"
            min={1}
            value={maxPerOrder}
            onChange={(e) => setMaxPerOrder(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="ticket-sales-start">Sales start</FieldLabel>
          <Input
            id="ticket-sales-start"
            type="datetime-local"
            value={salesStart}
            onChange={(e) => setSalesStart(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="ticket-sales-end">Sales end</FieldLabel>
          <Input
            id="ticket-sales-end"
            type="datetime-local"
            value={salesEnd}
            onChange={(e) => setSalesEnd(e.target.value)}
          />
        </Field>
        <Field orientation="horizontal">
          <Checkbox
            id="ticket-hidden"
            checked={isHidden}
            onCheckedChange={(checked) => setIsHidden(checked === true)}
          />
          <FieldLabel htmlFor="ticket-hidden">Hidden</FieldLabel>
        </Field>
        {createTicketType.isError && (
          <FieldError>{getErrorMessage(createTicketType.error)}</FieldError>
        )}
        <Button type="submit" disabled={createTicketType.isPending}>
          Add ticket type
        </Button>
      </FieldGroup>
    </form>
  )
}

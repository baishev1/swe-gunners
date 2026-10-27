import { type FormEvent, useState } from 'react'

import type { EventItem, EventVisibility } from '@/entities/event'
import { useVenues } from '@/entities/venue'
import { getErrorMessage } from '@/shared/api'
import { fromDateTimeInput, toDateTimeInput } from '@/shared/lib/format'
import { Button } from '@/shared/ui/button'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Textarea } from '@/shared/ui/textarea'

import { useSaveEvent } from '../model/use-save-event'

interface EventFormProps {
  event?: EventItem
  onSaved?: (event: EventItem) => void
}

export function EventForm({ event, onSaved }: EventFormProps) {
  const venues = useVenues()
  const saveEvent = useSaveEvent(event?.id)
  const [title, setTitle] = useState(event?.title ?? '')
  const [description, setDescription] = useState(event?.description ?? '')
  const [category, setCategory] = useState(event?.category ?? '')
  const [venueId, setVenueId] = useState(event?.venue_id ?? '')
  const [startTime, setStartTime] = useState(toDateTimeInput(event?.start_time ?? null))
  const [endTime, setEndTime] = useState(toDateTimeInput(event?.end_time ?? null))
  const [capacity, setCapacity] = useState(event ? String(event.capacity) : '')
  const [visibility, setVisibility] = useState<EventVisibility>(event?.visibility ?? 'public')
  const [registrationStart, setRegistrationStart] = useState(
    toDateTimeInput(event?.registration_start_time ?? null),
  )
  const [registrationEnd, setRegistrationEnd] = useState(
    toDateTimeInput(event?.registration_end_time ?? null),
  )
  const [coverImageUrl, setCoverImageUrl] = useState(event?.cover_image_url ?? '')

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    saveEvent.mutate(
      {
        title,
        description: description || null,
        category,
        venue_id: venueId,
        start_time: fromDateTimeInput(startTime) ?? '',
        end_time: fromDateTimeInput(endTime) ?? '',
        capacity: Number(capacity),
        visibility,
        registration_start_time: fromDateTimeInput(registrationStart),
        registration_end_time: fromDateTimeInput(registrationEnd),
        cover_image_url: coverImageUrl || null,
      },
      { onSuccess: (saved) => onSaved?.(saved) },
    )
  }

  return (
    <form onSubmit={handleSubmit}>
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="event-title">Title</FieldLabel>
          <Input
            id="event-title"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-description">Description</FieldLabel>
          <Textarea
            id="event-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-category">Category</FieldLabel>
          <Input
            id="event-category"
            required
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-venue">Venue</FieldLabel>
          <NativeSelect
            id="event-venue"
            className="w-full"
            required
            value={venueId}
            onChange={(e) => setVenueId(e.target.value)}
          >
            <NativeSelectOption value="">Select a venue</NativeSelectOption>
            {venues.data?.map((venue) => (
              <NativeSelectOption key={venue.id} value={venue.id}>
                {venue.name}, {venue.address}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="event-start">Starts</FieldLabel>
          <Input
            id="event-start"
            type="datetime-local"
            required
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-end">Ends</FieldLabel>
          <Input
            id="event-end"
            type="datetime-local"
            required
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-capacity">Capacity</FieldLabel>
          <Input
            id="event-capacity"
            type="number"
            min={1}
            required
            value={capacity}
            onChange={(e) => setCapacity(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-visibility">Visibility</FieldLabel>
          <NativeSelect
            id="event-visibility"
            className="w-full"
            value={visibility}
            onChange={(e) => setVisibility(e.target.value as EventVisibility)}
          >
            <NativeSelectOption value="public">Public</NativeSelectOption>
            <NativeSelectOption value="unlisted">Unlisted</NativeSelectOption>
            <NativeSelectOption value="private">Private</NativeSelectOption>
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="event-registration-start">Registration opens</FieldLabel>
          <Input
            id="event-registration-start"
            type="datetime-local"
            value={registrationStart}
            onChange={(e) => setRegistrationStart(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-registration-end">Registration closes</FieldLabel>
          <Input
            id="event-registration-end"
            type="datetime-local"
            value={registrationEnd}
            onChange={(e) => setRegistrationEnd(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-cover">Cover image URL</FieldLabel>
          <Input
            id="event-cover"
            type="url"
            value={coverImageUrl}
            onChange={(e) => setCoverImageUrl(e.target.value)}
          />
        </Field>
        {saveEvent.isError && <FieldError>{getErrorMessage(saveEvent.error)}</FieldError>}
        <Button type="submit" disabled={saveEvent.isPending}>
          {event ? 'Save changes' : 'Create event'}
        </Button>
      </FieldGroup>
    </form>
  )
}

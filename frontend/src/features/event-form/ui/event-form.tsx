import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation()
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
  const [refundPolicy, setRefundPolicy] = useState(event?.refund_policy ?? '')

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
        refund_policy: refundPolicy || null,
      },
      { onSuccess: (saved) => onSaved?.(saved) },
    )
  }

  return (
    <form onSubmit={handleSubmit}>
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="event-title">{t('eventForm.title')}</FieldLabel>
          <Input
            id="event-title"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-description">{t('eventForm.description')}</FieldLabel>
          <Textarea
            id="event-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-category">{t('eventForm.category')}</FieldLabel>
          <Input
            id="event-category"
            required
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-venue">{t('eventForm.venue')}</FieldLabel>
          <NativeSelect
            id="event-venue"
            className="w-full"
            required
            value={venueId}
            onChange={(e) => setVenueId(e.target.value)}
          >
            <NativeSelectOption value="">{t('eventForm.selectVenue')}</NativeSelectOption>
            {venues.data?.map((venue) => (
              <NativeSelectOption key={venue.id} value={venue.id}>
                {venue.name}, {venue.address}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="event-start">{t('eventForm.starts')}</FieldLabel>
          <Input
            id="event-start"
            type="datetime-local"
            required
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-end">{t('eventForm.ends')}</FieldLabel>
          <Input
            id="event-end"
            type="datetime-local"
            required
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-capacity">{t('eventForm.capacity')}</FieldLabel>
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
          <FieldLabel htmlFor="event-visibility">{t('eventForm.visibility')}</FieldLabel>
          <NativeSelect
            id="event-visibility"
            className="w-full"
            value={visibility}
            onChange={(e) => setVisibility(e.target.value as EventVisibility)}
          >
            <NativeSelectOption value="public">{t('eventForm.public')}</NativeSelectOption>
            <NativeSelectOption value="unlisted">{t('eventForm.unlisted')}</NativeSelectOption>
            <NativeSelectOption value="private">{t('eventForm.private')}</NativeSelectOption>
          </NativeSelect>
        </Field>
        <Field>
          <FieldLabel htmlFor="event-registration-start">
            {t('eventForm.registrationOpens')}
          </FieldLabel>
          <Input
            id="event-registration-start"
            type="datetime-local"
            value={registrationStart}
            onChange={(e) => setRegistrationStart(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-registration-end">
            {t('eventForm.registrationCloses')}
          </FieldLabel>
          <Input
            id="event-registration-end"
            type="datetime-local"
            value={registrationEnd}
            onChange={(e) => setRegistrationEnd(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-cover">{t('eventForm.coverImageUrl')}</FieldLabel>
          <Input
            id="event-cover"
            type="url"
            value={coverImageUrl}
            onChange={(e) => setCoverImageUrl(e.target.value)}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="event-refund-policy">{t('eventForm.refundPolicy')}</FieldLabel>
          <Textarea
            id="event-refund-policy"
            value={refundPolicy}
            onChange={(e) => setRefundPolicy(e.target.value)}
          />
        </Field>
        {saveEvent.isError && <FieldError>{getErrorMessage(saveEvent.error)}</FieldError>}
        <Button type="submit" disabled={saveEvent.isPending}>
          {event ? t('eventForm.saveChanges') : t('eventForm.create')}
        </Button>
      </FieldGroup>
    </form>
  )
}

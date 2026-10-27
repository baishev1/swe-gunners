import { useTranslation } from 'react-i18next'
import { type FormEvent, useState } from 'react'

import type { DiscountType } from '@/entities/promo-campaign'
import { useTicketTypes } from '@/entities/ticket-type'
import { getErrorMessage } from '@/shared/api'
import { fromDateTimeInput } from '@/shared/lib/format'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'

import { useCreatePromoCampaign } from '../model/use-promo-campaign-mutations'

export function PromoCampaignForm({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const createCampaign = useCreatePromoCampaign(eventId)
  const ticketTypes = useTicketTypes(eventId, true)
  const [name, setName] = useState('')
  const [discountType, setDiscountType] = useState<DiscountType>('percent')
  const [discountValue, setDiscountValue] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [maxRedemptions, setMaxRedemptions] = useState('')
  const [ticketTypeIds, setTicketTypeIds] = useState<string[]>([])

  function toggleTicketType(id: string, checked: boolean) {
    setTicketTypeIds((ids) => (checked ? [...ids, id] : ids.filter((other) => other !== id)))
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const value = Number(discountValue)
    createCampaign.mutate(
      {
        name,
        discount_type: discountType,
        // Fixed discounts are typed in tenge and stored in tiyn.
        discount_value: discountType === 'fixed' ? Math.round(value * 100) : value,
        start_time: fromDateTimeInput(startTime),
        end_time: fromDateTimeInput(endTime),
        max_redemptions: maxRedemptions ? Number(maxRedemptions) : null,
        ticket_type_ids: ticketTypeIds,
      },
      {
        onSuccess: () => {
          setName('')
          setDiscountValue('')
          setStartTime('')
          setEndTime('')
          setMaxRedemptions('')
          setTicketTypeIds([])
        },
      },
    )
  }

  return (
    <form onSubmit={handleSubmit}>
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="campaign-name">{t('promoCampaigns.name')}</FieldLabel>
          <Input
            id="campaign-name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field>
            <FieldLabel htmlFor="campaign-discount-type">
              {t('promoCampaigns.discountType')}
            </FieldLabel>
            <NativeSelect
              id="campaign-discount-type"
              value={discountType}
              onChange={(e) => setDiscountType(e.target.value as DiscountType)}
            >
              <NativeSelectOption value="percent">{t('promoCampaigns.percent')}</NativeSelectOption>
              <NativeSelectOption value="fixed">{t('promoCampaigns.fixed')}</NativeSelectOption>
            </NativeSelect>
          </Field>
          <Field>
            <FieldLabel htmlFor="campaign-discount-value">
              {discountType === 'percent'
                ? t('promoCampaigns.percentValue')
                : t('promoCampaigns.fixedValue')}
            </FieldLabel>
            <Input
              id="campaign-discount-value"
              type="number"
              required
              min={discountType === 'percent' ? 1 : 0.01}
              max={discountType === 'percent' ? 100 : undefined}
              step={discountType === 'percent' ? 1 : 0.01}
              value={discountValue}
              onChange={(e) => setDiscountValue(e.target.value)}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="campaign-start">{t('promoCampaigns.startTime')}</FieldLabel>
            <Input
              id="campaign-start"
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="campaign-end">{t('promoCampaigns.endTime')}</FieldLabel>
            <Input
              id="campaign-end"
              type="datetime-local"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
            />
          </Field>
        </div>
        <Field>
          <FieldLabel htmlFor="campaign-max-redemptions">
            {t('promoCampaigns.maxRedemptions')}
          </FieldLabel>
          <Input
            id="campaign-max-redemptions"
            type="number"
            min={1}
            value={maxRedemptions}
            onChange={(e) => setMaxRedemptions(e.target.value)}
          />
          <FieldDescription>{t('promoCampaigns.maxRedemptionsHint')}</FieldDescription>
        </Field>
        {ticketTypes.data && ticketTypes.data.length > 0 && (
          <FieldSet>
            <FieldLegend variant="label">{t('promoCampaigns.ticketTypes')}</FieldLegend>
            <FieldDescription>{t('promoCampaigns.ticketTypesHint')}</FieldDescription>
            <FieldGroup className="gap-3">
              {ticketTypes.data.map((ticketType) => (
                <Field key={ticketType.id} orientation="horizontal">
                  <Checkbox
                    id={`campaign-ticket-${ticketType.id}`}
                    checked={ticketTypeIds.includes(ticketType.id)}
                    onCheckedChange={(checked) => toggleTicketType(ticketType.id, checked === true)}
                  />
                  <FieldLabel htmlFor={`campaign-ticket-${ticketType.id}`}>
                    {ticketType.name}
                  </FieldLabel>
                </Field>
              ))}
            </FieldGroup>
          </FieldSet>
        )}
        {createCampaign.isError && <FieldError>{getErrorMessage(createCampaign.error)}</FieldError>}
        <Button type="submit" disabled={createCampaign.isPending}>
          {t('promoCampaigns.create')}
        </Button>
      </FieldGroup>
    </form>
  )
}

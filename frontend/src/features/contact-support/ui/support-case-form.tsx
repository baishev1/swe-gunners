import { useMemo, type FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import type { SupportCategory, SupportTarget } from '@/entities/support'
import { createSupportCase, SUPPORT_CATEGORIES } from '@/entities/support'
import { useEvent } from '@/entities/event'
import { useMe } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'

interface SupportCaseFormProps {
  eventId?: string
  orderId?: string
  ticketId?: string
  defaultCategory?: SupportCategory
}

export function SupportCaseForm({
  eventId,
  orderId,
  ticketId,
  defaultCategory,
}: SupportCaseFormProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { data: me, isPending: mePending } = useMe()
  const event = useEvent(eventId ?? '')

  const target: SupportTarget = useMemo(() => {
    const staff = me?.role === 'organizer' || me?.role === 'platform_admin'
    const ownsEvent = Boolean(event.data && me?.id === event.data.organizer_id)
    return staff && (eventId === undefined || ownsEvent) ? 'platform' : 'organizer'
  }, [event.data, eventId, me])

  const mutation = useMutation({
    mutationFn: createSupportCase,
    onSuccess: (supportCase) => {
      navigate(`${ROUTES.supportCase}?case_id=${supportCase.id}`)
    },
  })

  if (mePending) return <Skeleton className="h-64 w-full" />

  const canCreate = Boolean(me) && (eventId !== undefined || target === 'platform')
  if (!canCreate) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t('support.form.contextRequiredTitle')}</CardTitle>
          <CardDescription>{t('support.form.contextRequired')}</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  function handleSubmit(submitEvent: FormEvent<HTMLFormElement>) {
    submitEvent.preventDefault()
    const form = new FormData(submitEvent.currentTarget)
    mutation.mutate({
      target,
      event_id: eventId ?? null,
      order_id: orderId ?? null,
      ticket_id: ticketId ?? null,
      category: String(form.get('category')) as SupportCategory,
      subject: String(form.get('subject')),
      message: String(form.get('message')),
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('support.form.title')}</CardTitle>
        <CardDescription>
          {target === 'platform'
            ? t('support.form.platformDescription')
            : t('support.form.organizerDescription')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <FieldGroup className="gap-6">
            {eventId !== undefined && (
              <Field>
                <FieldLabel>{t('support.form.event')}</FieldLabel>
                {event.isPending ? (
                  <Skeleton className="h-5 w-48" />
                ) : event.isError ? (
                  <FieldError>{getErrorMessage(event.error)}</FieldError>
                ) : (
                  <p className="text-sm">{event.data?.title}</p>
                )}
              </Field>
            )}
            {(orderId || ticketId) && (
              <Field>
                <FieldLabel>{t('support.form.attached')}</FieldLabel>
                <p className="text-sm">
                  {[
                    orderId && t('support.context.order', { number: orderId.slice(0, 8) }),
                    ticketId && t('support.context.ticket', { number: ticketId.slice(0, 8) }),
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              </Field>
            )}
            <Field>
              <FieldLabel htmlFor="category">{t('support.form.category')}</FieldLabel>
              <NativeSelect
                id="category"
                name="category"
                defaultValue={defaultCategory ?? 'event_information'}
              >
                {SUPPORT_CATEGORIES.map((category) => (
                  <NativeSelectOption key={category} value={category}>
                    {t(`support.categories.${category}`)}
                  </NativeSelectOption>
                ))}
              </NativeSelect>
            </Field>
            <Field>
              <FieldLabel htmlFor="subject">{t('support.form.subject')}</FieldLabel>
              <Input id="subject" name="subject" required maxLength={200} />
            </Field>
            <Field>
              <FieldLabel htmlFor="message">{t('support.form.message')}</FieldLabel>
              <Textarea id="message" name="message" required rows={6} maxLength={5000} />
            </Field>
            {mutation.isError && <FieldError>{getErrorMessage(mutation.error)}</FieldError>}
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? t('support.form.submitting') : t('support.form.submit')}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  )
}

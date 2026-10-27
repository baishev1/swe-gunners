import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { fetchOrganizerProfile, updateOrganizerProfile } from '@/features/organizer-profile'
import type { OrganizerProfile } from '@/features/organizer-profile'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'

const PROFILE_QUERY_KEY = ['organizer-profile']

function ProfileForm({ profile }: { profile: OrganizerProfile }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: updateOrganizerProfile,
    onSuccess: (data) => queryClient.setQueryData(PROFILE_QUERY_KEY, data),
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    mutation.mutate({
      organization_name: String(form.get('organization_name')) || null,
      contact_email: String(form.get('contact_email')) || null,
      contact_phone: String(form.get('contact_phone')) || null,
      payout_recipient_name: String(form.get('payout_recipient_name')) || null,
      payout_iban: String(form.get('payout_iban')) || null,
      payout_bin: String(form.get('payout_bin')) || null,
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="organization_name">
            {t('organizerProfile.organizationName')}
          </FieldLabel>
          <Input
            id="organization_name"
            name="organization_name"
            defaultValue={profile.organization_name ?? ''}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="contact_email">{t('organizerProfile.contactEmail')}</FieldLabel>
          <Input
            id="contact_email"
            name="contact_email"
            type="email"
            defaultValue={profile.contact_email ?? ''}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="contact_phone">{t('organizerProfile.contactPhone')}</FieldLabel>
          <Input
            id="contact_phone"
            name="contact_phone"
            type="tel"
            defaultValue={profile.contact_phone ?? ''}
          />
        </Field>
        <h2 className="text-sm font-medium">{t('organizerProfile.payout')}</h2>
        <Field>
          <FieldLabel htmlFor="payout_recipient_name">
            {t('organizerProfile.payoutRecipientName')}
          </FieldLabel>
          <Input
            id="payout_recipient_name"
            name="payout_recipient_name"
            defaultValue={profile.payout_recipient_name ?? ''}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="payout_iban">{t('organizerProfile.payoutIban')}</FieldLabel>
          <Input id="payout_iban" name="payout_iban" defaultValue={profile.payout_iban ?? ''} />
        </Field>
        <Field>
          <FieldLabel htmlFor="payout_bin">{t('organizerProfile.payoutBin')}</FieldLabel>
          <Input id="payout_bin" name="payout_bin" defaultValue={profile.payout_bin ?? ''} />
        </Field>
        {mutation.isError && <FieldError>{getErrorMessage(mutation.error)}</FieldError>}
        {mutation.isSuccess && (
          <p className="text-muted-foreground text-sm">{t('organizerProfile.saved')}</p>
        )}
        <Button type="submit" disabled={mutation.isPending}>
          {t('organizerProfile.save')}
        </Button>
      </FieldGroup>
    </form>
  )
}

export function OrganizerProfilePage() {
  const { t } = useTranslation()
  const { data, isPending, isError, error } = useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: fetchOrganizerProfile,
  })

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{t('organizerProfile.title')}</CardTitle>
          <CardDescription>{t('organizerProfile.description')}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {isPending && (
            <p className="text-muted-foreground text-sm">{t('organizerProfile.loading')}</p>
          )}
          {isError && <FieldError>{getErrorMessage(error)}</FieldError>}
          {data && <ProfileForm profile={data} />}
          <Link to={ROUTES.home} className="text-sm underline">
            {t('common.backToHome')}
          </Link>
        </CardContent>
      </Card>
    </main>
  )
}

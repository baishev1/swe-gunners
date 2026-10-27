import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
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
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="organization_name">Organization name</FieldLabel>
          <Input
            id="organization_name"
            name="organization_name"
            defaultValue={profile.organization_name ?? ''}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="contact_email">Contact email</FieldLabel>
          <Input
            id="contact_email"
            name="contact_email"
            type="email"
            defaultValue={profile.contact_email ?? ''}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="contact_phone">Contact phone</FieldLabel>
          <Input
            id="contact_phone"
            name="contact_phone"
            type="tel"
            defaultValue={profile.contact_phone ?? ''}
          />
        </Field>
        {mutation.isError && <FieldError>{getErrorMessage(mutation.error)}</FieldError>}
        {mutation.isSuccess && <p className="text-muted-foreground text-sm">Saved.</p>}
        <Button type="submit" disabled={mutation.isPending}>
          Save
        </Button>
      </FieldGroup>
    </form>
  )
}

export function OrganizerProfilePage() {
  const { data, isPending, isError, error } = useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: fetchOrganizerProfile,
  })

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Organizer profile</CardTitle>
          <CardDescription>How attendees can reach you.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {isPending && <p className="text-muted-foreground text-sm">Loading...</p>}
          {isError && <FieldError>{getErrorMessage(error)}</FieldError>}
          {data && <ProfileForm profile={data} />}
          <Link to={ROUTES.home} className="text-sm underline">
            Back to home
          </Link>
        </CardContent>
      </Card>
    </main>
  )
}

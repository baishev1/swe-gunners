import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { register } from '@/features/auth'
import type { RegisterRole } from '@/features/auth'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'

export function RegisterPage() {
  const { t } = useTranslation()
  const [role, setRole] = useState<RegisterRole>('attendee')
  const mutation = useMutation({ mutationFn: register })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    mutation.mutate({
      email: String(form.get('email')),
      password: String(form.get('password')),
      full_name: String(form.get('full_name')),
      role,
    })
  }

  if (mutation.isSuccess) {
    return (
      <main className="flex min-h-svh items-center justify-center p-4">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>{t('register.checkEmailTitle')}</CardTitle>
            <CardDescription>
              {t('register.checkEmailDescription', { email: mutation.data.email })}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link to={ROUTES.login} className="text-sm underline">
              {t('common.goToSignIn')}
            </Link>
          </CardContent>
        </Card>
      </main>
    )
  }

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{t('register.title')}</CardTitle>
          <CardDescription>{t('register.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <FieldGroup>
              <Field>
                <FieldLabel>{t('register.roleLabel')}</FieldLabel>
                <ToggleGroup
                  type="single"
                  variant="outline"
                  value={role}
                  onValueChange={(value) => value && setRole(value as RegisterRole)}
                >
                  <ToggleGroupItem value="attendee">{t('register.attendee')}</ToggleGroupItem>
                  <ToggleGroupItem value="organizer">{t('register.organizer')}</ToggleGroupItem>
                </ToggleGroup>
              </Field>
              <Field>
                <FieldLabel htmlFor="full_name">{t('register.fullName')}</FieldLabel>
                <Input id="full_name" name="full_name" required />
              </Field>
              <Field>
                <FieldLabel htmlFor="email">{t('common.email')}</FieldLabel>
                <Input id="email" name="email" type="email" required />
              </Field>
              <Field>
                <FieldLabel htmlFor="password">{t('common.password')}</FieldLabel>
                <Input id="password" name="password" type="password" minLength={8} required />
              </Field>
              {mutation.isError && <FieldError>{getErrorMessage(mutation.error)}</FieldError>}
              <Button type="submit" disabled={mutation.isPending}>
                {t('register.submit')}
              </Button>
              <Link to={ROUTES.login} className="text-sm underline">
                {t('register.haveAccount')}
              </Link>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}

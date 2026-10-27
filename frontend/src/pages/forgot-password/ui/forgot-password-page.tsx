import { useMutation } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { forgotPassword } from '@/features/auth'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'

export function ForgotPasswordPage() {
  const { t } = useTranslation()
  const mutation = useMutation({ mutationFn: forgotPassword })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    mutation.mutate(String(form.get('email')))
  }

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{t('forgotPassword.title')}</CardTitle>
          <CardDescription>
            {mutation.isSuccess
              ? t('forgotPassword.descriptionSent')
              : t('forgotPassword.description')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="email">{t('common.email')}</FieldLabel>
                <Input id="email" name="email" type="email" required />
              </Field>
              {mutation.isError && <FieldError>{getErrorMessage(mutation.error)}</FieldError>}
              <Button type="submit" disabled={mutation.isPending}>
                {t('forgotPassword.submit')}
              </Button>
              <Link to={ROUTES.login} className="text-sm underline">
                {t('forgotPassword.backToSignIn')}
              </Link>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}

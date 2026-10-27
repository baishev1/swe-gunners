import { useMutation } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { resetPassword } from '@/features/auth'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'

export function ResetPasswordPage() {
  const { t } = useTranslation()
  const [params] = useSearchParams()
  const token = params.get('token')
  const mutation = useMutation({ mutationFn: resetPassword })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (token === null) return
    const form = new FormData(event.currentTarget)
    mutation.mutate({ token, new_password: String(form.get('new_password')) })
  }

  if (token === null) {
    return (
      <main className="flex min-h-svh items-center justify-center p-4">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>{t('common.invalidLink')}</CardTitle>
            <CardDescription>{t('resetPassword.missingToken')}</CardDescription>
          </CardHeader>
          <CardContent>
            <Link to={ROUTES.forgotPassword} className="text-sm underline">
              {t('resetPassword.requestNewLink')}
            </Link>
          </CardContent>
        </Card>
      </main>
    )
  }

  if (mutation.isSuccess) {
    return (
      <main className="flex min-h-svh items-center justify-center p-4">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>{t('resetPassword.successTitle')}</CardTitle>
            <CardDescription>{t('resetPassword.successDescription')}</CardDescription>
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
          <CardTitle>{t('resetPassword.title')}</CardTitle>
          <CardDescription>{t('resetPassword.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="new_password">{t('resetPassword.newPassword')}</FieldLabel>
                <Input
                  id="new_password"
                  name="new_password"
                  type="password"
                  minLength={8}
                  required
                />
              </Field>
              {mutation.isError && <FieldError>{getErrorMessage(mutation.error)}</FieldError>}
              <Button type="submit" disabled={mutation.isPending}>
                {t('resetPassword.submit')}
              </Button>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}

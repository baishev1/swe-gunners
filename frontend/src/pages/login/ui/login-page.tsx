import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'

import { login } from '@/features/auth'
import { getErrorMessage, setToken } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'

export function LoginPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: login,
    onSuccess: ({ access_token }) => {
      setToken(access_token)
      queryClient.clear()
      navigate(ROUTES.home)
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    mutation.mutate({
      email: String(form.get('email')),
      password: String(form.get('password')),
    })
  }

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{t('login.title')}</CardTitle>
          <CardDescription>{t('login.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="email">{t('common.email')}</FieldLabel>
                <Input id="email" name="email" type="email" required />
              </Field>
              <Field>
                <FieldLabel htmlFor="password">{t('common.password')}</FieldLabel>
                <Input id="password" name="password" type="password" required />
              </Field>
              {mutation.isError && <FieldError>{getErrorMessage(mutation.error)}</FieldError>}
              <Button type="submit" disabled={mutation.isPending}>
                {t('login.submit')}
              </Button>
              <div className="flex justify-between text-sm">
                <Link to={ROUTES.register} className="underline">
                  {t('login.createAccount')}
                </Link>
                <Link to={ROUTES.forgotPassword} className="underline">
                  {t('login.forgotPassword')}
                </Link>
              </div>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </main>
  )
}

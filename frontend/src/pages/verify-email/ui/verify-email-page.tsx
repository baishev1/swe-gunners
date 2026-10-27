import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { verifyEmail } from '@/features/auth'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'

export function VerifyEmailPage() {
  const { t } = useTranslation()
  const [params] = useSearchParams()
  const token = params.get('token')

  const { isPending, isError, error } = useQuery({
    queryKey: ['verify-email', token],
    queryFn: () => verifyEmail(token ?? ''),
    enabled: token !== null,
    retry: false,
  })

  let title = t('verifyEmail.pendingTitle')
  let message = t('verifyEmail.pendingMessage')
  if (token === null) {
    title = t('common.invalidLink')
    message = t('verifyEmail.missingToken')
  } else if (isError) {
    title = t('verifyEmail.failedTitle')
    message = getErrorMessage(error)
  } else if (!isPending) {
    title = t('verifyEmail.successTitle')
    message = t('verifyEmail.successMessage')
  }

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>{message}</CardDescription>
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

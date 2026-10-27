import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'

import { verifyEmail } from '@/features/auth'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'

export function VerifyEmailPage() {
  const [params] = useSearchParams()
  const token = params.get('token')

  const { isPending, isError, error } = useQuery({
    queryKey: ['verify-email', token],
    queryFn: () => verifyEmail(token ?? ''),
    enabled: token !== null,
    retry: false,
  })

  let title = 'Verifying your email'
  let message = 'One moment.'
  if (token === null) {
    title = 'Invalid link'
    message = 'The verification token is missing.'
  } else if (isError) {
    title = 'Verification failed'
    message = getErrorMessage(error)
  } else if (!isPending) {
    title = 'Email verified'
    message = 'Your email address is confirmed.'
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
            Go to sign in
          </Link>
        </CardContent>
      </Card>
    </main>
  )
}

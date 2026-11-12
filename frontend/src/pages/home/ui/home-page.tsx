import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { resendVerification } from '@/features/auth'
import { useLogout, useMe } from '@/entities/session'
import { ROUTES, env } from '@/shared/config'
import { Button } from '@/shared/ui/button'

export function HomePage() {
  const { t } = useTranslation()
  const { data: me } = useMe()
  const logout = useLogout()
  const resend = useMutation({ mutationFn: resendVerification })

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-2">
      <h1 className="text-2xl font-semibold">{env.appName}</h1>
      <p className="text-muted-foreground text-sm">{t('home.tagline')}</p>
      {me && !me.is_email_verified && (
        <div className="flex flex-col items-center gap-2">
          <p className="text-sm">{t('home.verifyEmail')}</p>
          {resend.isSuccess ? (
            <p className="text-muted-foreground text-sm">{t('home.verificationSent')}</p>
          ) : (
            <Button variant="outline" onClick={() => resend.mutate()} disabled={resend.isPending}>
              {t('home.resendVerification')}
            </Button>
          )}
        </div>
      )}
      {me?.role === 'organizer' && (
        <>
          <Link to={ROUTES.organizerDashboard} className="text-sm underline">
            {t('home.organizerDashboard')}
          </Link>
          <Link to={ROUTES.organizerProfile} className="text-sm underline">
            {t('home.organizerProfile')}
          </Link>
        </>
      )}
      {me && (
        <Link to={ROUTES.support} className="text-sm underline">
          {t('support.title')}
        </Link>
      )}
      <Button variant="outline" onClick={logout}>
        {t('home.signOut')}
      </Button>
    </main>
  )
}

import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { useLogout, useMe } from '@/entities/session'
import { ROUTES, env } from '@/shared/config'
import { Button } from '@/shared/ui/button'

export function HomePage() {
  const { t } = useTranslation()
  const { data: me } = useMe()
  const logout = useLogout()

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-2">
      <h1 className="text-2xl font-semibold">{env.appName}</h1>
      <p className="text-muted-foreground text-sm">{t('home.tagline')}</p>
      {me?.role === 'organizer' && (
        <Link to={ROUTES.organizerProfile} className="text-sm underline">
          {t('home.organizerProfile')}
        </Link>
      )}
      <Button variant="outline" onClick={logout}>
        {t('home.signOut')}
      </Button>
    </main>
  )
}

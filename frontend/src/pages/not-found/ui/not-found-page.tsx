import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { ROUTES } from '@/shared/config'

export function NotFoundPage() {
  const { t } = useTranslation()
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-2">
      <h1 className="text-2xl font-semibold">404</h1>
      <Link className="text-muted-foreground text-sm underline" to={ROUTES.home}>
        {t('common.backToHome')}
      </Link>
    </main>
  )
}

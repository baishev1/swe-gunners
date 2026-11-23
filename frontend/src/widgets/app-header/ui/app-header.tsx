import { ArrowLeft, House } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { env, ROUTES } from '@/shared/config'
import { Button } from '@/shared/ui/button'

import { LanguageSwitcher } from './language-switcher'

export function AppHeader() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()

  function goBack() {
    // A page opened from a link or a QR code has no history to go back to.
    if (location.key === 'default') navigate(ROUTES.home)
    else navigate(-1)
  }

  return (
    <header className="bg-background sticky top-0 z-10 border-b">
      <div className="mx-auto flex max-w-5xl items-center gap-1 px-4 py-2">
        {location.pathname !== ROUTES.home && (
          <Button variant="ghost" size="sm" onClick={goBack} aria-label={t('common.back')}>
            <ArrowLeft />
            <span className="hidden sm:inline">{t('common.back')}</span>
          </Button>
        )}
        <Button variant="ghost" size="sm" asChild>
          <Link to={ROUTES.home} aria-label={t('common.backToHome')}>
            <House />
            <span className="hidden sm:inline">{env.appName}</span>
          </Link>
        </Button>
        <div className="ml-auto">
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  )
}

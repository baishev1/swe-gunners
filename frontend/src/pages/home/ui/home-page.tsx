import { useMutation } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { EventCard, useEvents } from '@/entities/event'
import { useLogout, useMe } from '@/entities/session'
import { resendVerification } from '@/features/auth'
import { getErrorMessage } from '@/shared/api'
import { ROUTES, env } from '@/shared/config'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'

export function HomePage() {
  const { t } = useTranslation()
  const { data: me } = useMe()
  const logout = useLogout()
  const resend = useMutation({ mutationFn: resendVerification })
  const events = useEvents()
  const upcoming = events.data?.slice(0, 3) ?? []

  const isOrganizer = me?.role === 'organizer'
  const isAdmin = me?.role === 'platform_admin'

  const links = [
    { to: ROUTES.events, label: t('home.browseEvents') },
    ...(isOrganizer
      ? [
          { to: ROUTES.organizerDashboard, label: t('home.organizerDashboard') },
          { to: ROUTES.organizerProfile, label: t('home.organizerProfile') },
        ]
      : []),
    ...(isAdmin ? [{ to: ROUTES.admin, label: t('home.admin') }] : []),
    ...(!isOrganizer && !isAdmin
      ? [
          { to: ROUTES.orders, label: t('home.myOrders') },
          { to: ROUTES.tickets, label: t('home.myTickets') },
        ]
      : []),
    { to: ROUTES.support, label: t('support.title') },
  ]

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 pb-6 pt-16">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">{env.appName}</h1>
          <p className="text-muted-foreground text-sm">{t('home.tagline')}</p>
          {me && (
            <p className="text-muted-foreground text-sm">
              {me.full_name} · {me.email}
            </p>
          )}
        </div>
        <Button variant="outline" onClick={logout}>
          {t('home.signOut')}
        </Button>
      </header>

      {me && !me.is_email_verified && (
        <div className="flex flex-col items-start gap-2">
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

      <nav className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {links.map((link) => (
          <Link
            key={link.to}
            to={link.to}
            className="bg-card hover:bg-muted rounded-lg border p-4 text-sm font-medium transition-colors"
          >
            {link.label}
          </Link>
        ))}
      </nav>

      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold">{t('eventsList.title')}</h2>
          <Button variant="link" asChild className="px-0">
            <Link to={ROUTES.events}>{t('home.viewAll')}</Link>
          </Button>
        </div>
        {events.isPending && <Skeleton className="h-32 w-full" />}
        {events.isError && (
          <p className="text-destructive text-sm">{getErrorMessage(events.error)}</p>
        )}
        {events.data?.length === 0 && (
          <p className="text-muted-foreground text-sm">{t('eventsList.empty')}</p>
        )}
        {upcoming.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {upcoming.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

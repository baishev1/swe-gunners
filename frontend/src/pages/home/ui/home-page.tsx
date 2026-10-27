import { Link } from 'react-router-dom'

import { useLogout, useMe } from '@/entities/session'
import { ROUTES, env } from '@/shared/config'
import { Button } from '@/shared/ui/button'

export function HomePage() {
  const { data: me } = useMe()
  const logout = useLogout()

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-2">
      <h1 className="text-2xl font-semibold">{env.appName}</h1>
      <p className="text-muted-foreground text-sm">Event ticketing platform</p>
      {me?.role === 'organizer' && (
        <Link to={ROUTES.organizerProfile} className="text-sm underline">
          Organizer profile
        </Link>
      )}
      <Button variant="outline" onClick={logout}>
        Sign out
      </Button>
    </main>
  )
}

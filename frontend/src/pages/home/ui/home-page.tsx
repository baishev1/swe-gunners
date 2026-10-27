import { Link } from 'react-router-dom'
import { env } from '@/shared/config'
import { Button } from '@/shared/ui'

export function HomePage() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4 text-center px-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{env.appName}</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Event ticketing platform for Kazakhstan
        </p>
      </div>
      <div className="flex gap-3">
        <Button asChild>
          <Link to="/checkout">Buy Tickets</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/orders">My Orders</Link>
        </Button>
      </div>
    </main>
  )
}

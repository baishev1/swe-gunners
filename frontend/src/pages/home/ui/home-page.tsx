import { env } from '@/shared/config'

export function HomePage() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-2">
      <h1 className="text-2xl font-semibold">{env.appName}</h1>
      <p className="text-muted-foreground text-sm">Event ticketing platform</p>
    </main>
  )
}

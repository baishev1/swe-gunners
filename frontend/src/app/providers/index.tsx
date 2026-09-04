import type { ReactNode } from 'react'
import { BrowserRouter } from 'react-router-dom'

import { QueryProvider } from './query-provider'

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <BrowserRouter>
      <QueryProvider>{children}</QueryProvider>
    </BrowserRouter>
  )
}

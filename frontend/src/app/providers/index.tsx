import type { ReactNode } from 'react'
import { BrowserRouter } from 'react-router-dom'

import '@/shared/i18n'
import { AppHeader } from '@/widgets/app-header'

import { QueryProvider } from './query-provider'

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <BrowserRouter>
      <QueryProvider>
        <AppHeader />
        {children}
      </QueryProvider>
    </BrowserRouter>
  )
}

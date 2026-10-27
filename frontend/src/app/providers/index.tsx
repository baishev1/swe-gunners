import type { ReactNode } from 'react'
import { BrowserRouter } from 'react-router-dom'

import '@/shared/i18n'
import { LanguageSwitcher } from '@/widgets/language-switcher'

import { QueryProvider } from './query-provider'

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <BrowserRouter>
      <QueryProvider>
        <LanguageSwitcher />
        {children}
      </QueryProvider>
    </BrowserRouter>
  )
}

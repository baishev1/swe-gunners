import { Route, Routes } from 'react-router-dom'

import { HomePage } from '@/pages/home'
import { NotFoundPage } from '@/pages/not-found'
import { ROUTES } from '@/shared/config'

export function AppRouter() {
  return (
    <Routes>
      <Route path={ROUTES.home} element={<HomePage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

import { Route, Routes } from 'react-router-dom'

import { CheckoutPage } from '@/pages/checkout'
import { HomePage } from '@/pages/home'
import { NotFoundPage } from '@/pages/not-found'
import { OrdersPage } from '@/pages/orders'
import { TicketsPage } from '@/pages/tickets'
import { ROUTES } from '@/shared/config'

export function AppRouter() {
  return (
    <Routes>
      <Route path={ROUTES.home} element={<HomePage />} />
      <Route path={ROUTES.checkout} element={<CheckoutPage />} />
      <Route path={ROUTES.orders} element={<OrdersPage />} />
      <Route path={ROUTES.tickets} element={<TicketsPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

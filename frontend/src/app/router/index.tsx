import { Route, Routes } from 'react-router-dom'

import { AdminPage } from '@/pages/admin'
import { ForgotPasswordPage } from '@/pages/forgot-password'
import { EventDetailPage } from '@/pages/event-detail'
import { EventHistoryPage } from '@/pages/event-history'
import { CheckoutPage } from '@/pages/checkout'
import { EventsListPage } from '@/pages/events-list'
import { HomePage } from '@/pages/home'
import { LoginPage } from '@/pages/login'
import { NotFoundPage } from '@/pages/not-found'
import { OrdersPage } from '@/pages/orders'
import { OrganizerProfilePage } from '@/pages/organizer-profile'
import { RegisterPage } from '@/pages/register'
import { ResetPasswordPage } from '@/pages/reset-password'
import { TicketsPage } from '@/pages/tickets'
import { VerifyEmailPage } from '@/pages/verify-email'
import { OrganizerEventEditPage } from '@/pages/organizer-event-edit'
import { OrganizerEventNewPage } from '@/pages/organizer-event-new'
import { OrganizerEventPromoPage } from '@/pages/organizer-event-promo'
import { ROUTES } from '@/shared/config'

import { ProtectedRoute } from './protected-route'

export function AppRouter() {
  return (
    <Routes>
      <Route path={ROUTES.login} element={<LoginPage />} />
      <Route path={ROUTES.register} element={<RegisterPage />} />
      <Route path={ROUTES.verifyEmail} element={<VerifyEmailPage />} />
      <Route path={ROUTES.forgotPassword} element={<ForgotPasswordPage />} />
      <Route path={ROUTES.resetPassword} element={<ResetPasswordPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path={ROUTES.home} element={<HomePage />} />
        <Route path={ROUTES.eventHistory} element={<EventHistoryPage />} />
        <Route path={ROUTES.checkout} element={<CheckoutPage />} />
        <Route path={ROUTES.orders} element={<OrdersPage />} />
        <Route path={ROUTES.tickets} element={<TicketsPage />} />
      </Route>
      <Route element={<ProtectedRoute role="organizer" />}>
        <Route path={ROUTES.organizerProfile} element={<OrganizerProfilePage />} />
      </Route>
      <Route path={ROUTES.events} element={<EventsListPage />} />
      <Route path={ROUTES.eventDetail} element={<EventDetailPage />} />
      <Route element={<ProtectedRoute role="organizer" />}>
        <Route path={ROUTES.organizerEventNew} element={<OrganizerEventNewPage />} />
        <Route path={ROUTES.organizerEventEdit} element={<OrganizerEventEditPage />} />
        <Route path={ROUTES.organizerEventPromo} element={<OrganizerEventPromoPage />} />
      </Route>
      <Route element={<ProtectedRoute role="platform_admin" />}>
        <Route path={ROUTES.admin} element={<AdminPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

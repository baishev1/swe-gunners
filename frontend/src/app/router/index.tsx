import { Route, Routes } from 'react-router-dom'

import { ForgotPasswordPage } from '@/pages/forgot-password'
import { HomePage } from '@/pages/home'
import { LoginPage } from '@/pages/login'
import { NotFoundPage } from '@/pages/not-found'
import { OrganizerProfilePage } from '@/pages/organizer-profile'
import { RegisterPage } from '@/pages/register'
import { ResetPasswordPage } from '@/pages/reset-password'
import { VerifyEmailPage } from '@/pages/verify-email'
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
      </Route>
      <Route element={<ProtectedRoute role="organizer" />}>
        <Route path={ROUTES.organizerProfile} element={<OrganizerProfilePage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

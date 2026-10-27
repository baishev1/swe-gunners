import { Navigate, Outlet } from 'react-router-dom'

import { useMe } from '@/entities/session'
import type { Role } from '@/entities/session'
import { getToken } from '@/shared/api'
import { ROUTES } from '@/shared/config'

export function ProtectedRoute({ role }: { role?: Role }) {
  const { data: me, isPending } = useMe()

  if (getToken() === null) return <Navigate to={ROUTES.login} replace />
  if (isPending) return null
  if (!me) return <Navigate to={ROUTES.login} replace />
  if (role && me.role !== role) return <Navigate to={ROUTES.home} replace />

  return <Outlet />
}

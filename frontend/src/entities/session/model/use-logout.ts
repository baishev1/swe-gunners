import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { clearToken } from '@/shared/api'
import { ROUTES } from '@/shared/config'

export function useLogout() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  return function logout() {
    clearToken()
    queryClient.clear()
    navigate(ROUTES.login)
  }
}

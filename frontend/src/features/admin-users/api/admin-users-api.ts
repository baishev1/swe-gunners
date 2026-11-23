import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type { Role } from '@/entities/session'
import { apiClient } from '@/shared/api'

export interface AdminUser {
  id: string
  email: string
  full_name: string
  role: Role
  is_active: boolean
  is_email_verified: boolean
  created_at: string
}

const adminUserKeys = {
  all: ['admin', 'users'] as const,
  search: (q: string, role: string) => [...adminUserKeys.all, q, role] as const,
}

export function useAdminUsers(q: string, role: string) {
  return useQuery({
    queryKey: adminUserKeys.search(q, role),
    queryFn: async () =>
      (
        await apiClient.get<AdminUser[]>('/admin/users', {
          params: { q: q || undefined, role: role || undefined },
        })
      ).data,
  })
}

export function useSuspendUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (userId: string) =>
      (
        await apiClient.post<AdminUser>('/admin/users/suspend', null, {
          params: { user_id: userId },
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: adminUserKeys.all }),
  })
}

export function useReinstateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (userId: string) =>
      (
        await apiClient.post<AdminUser>('/admin/users/reinstate', null, {
          params: { user_id: userId },
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: adminUserKeys.all }),
  })
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

export interface PlatformSettings {
  activation_fee: number
  updated_at: string
}

const platformSettingsKey = ['admin', 'settings'] as const

export function usePlatformSettings() {
  return useQuery({
    queryKey: platformSettingsKey,
    queryFn: async () => (await apiClient.get<PlatformSettings>('/admin/settings')).data,
  })
}

export function useUpdatePlatformSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: { activation_fee: number }) =>
      (await apiClient.patch<PlatformSettings>('/admin/settings', payload)).data,
    onSuccess: (settings) => queryClient.setQueryData(platformSettingsKey, settings),
  })
}

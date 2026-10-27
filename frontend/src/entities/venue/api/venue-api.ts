import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { Venue } from '../model/types'

export const venueKeys = {
  all: ['venues'] as const,
}

export function useVenues() {
  return useQuery({
    queryKey: venueKeys.all,
    queryFn: async () => (await apiClient.get<Venue[]>('/venues')).data,
  })
}

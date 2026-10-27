import { useQuery } from '@tanstack/react-query'

import { getToken } from '@/shared/api'

import { fetchMe } from '../api/session-api'

export const ME_QUERY_KEY = ['me']

export function useMe() {
  return useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: fetchMe,
    enabled: getToken() !== null,
    retry: false,
  })
}

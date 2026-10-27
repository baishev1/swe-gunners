import { apiClient } from '@/shared/api'

import type { User } from '../model/types'

export async function fetchMe() {
  const { data } = await apiClient.get<User>('/api/v1/auth/me')
  return data
}

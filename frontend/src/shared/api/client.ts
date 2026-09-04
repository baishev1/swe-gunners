import axios from 'axios'

import { env } from '@/shared/config'

export const apiClient = axios.create({
  baseURL: env.apiUrl,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

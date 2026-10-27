import axios from 'axios'

import { env } from '@/shared/config'

import { clearToken, getToken } from './token'

export const apiClient = axios.create({
  baseURL: env.apiUrl,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401 && getToken()) {
      clearToken()
      window.location.assign('/login')
    }
    return Promise.reject(error)
  },
)

import axios from 'axios'

import { env } from '@/shared/config'

import { clearToken, getRefreshToken, getToken, setToken } from './token'

declare module 'axios' {
  interface InternalAxiosRequestConfig {
    retried?: boolean
  }
}

type TokenPair = { access_token: string; refresh_token: string }

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
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401 || !getToken()) {
      return Promise.reject(error)
    }
    const config = error.config
    const refreshToken = getRefreshToken()
    if (config && !config.retried && refreshToken) {
      config.retried = true
      try {
        const { data } = await axios.post<TokenPair>(`${env.apiUrl}/auth/refresh`, {
          refresh_token: refreshToken,
        })
        setToken(data.access_token, data.refresh_token)
        return await apiClient(config)
      } catch {
        // The refresh token is gone or expired too; sign out below.
      }
    }
    clearToken()
    window.location.assign('/login')
    return Promise.reject(error)
  },
)

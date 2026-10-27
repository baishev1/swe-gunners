import { apiClient } from '@/shared/api'
import type { User } from '@/entities/session'

export type RegisterRole = 'attendee' | 'organizer'

type LoginBody = { email: string; password: string }

type RegisterBody = LoginBody & { full_name: string; role: RegisterRole }

type ResetPasswordBody = { token: string; new_password: string }

export async function login(body: LoginBody) {
  const { data } = await apiClient.post<{ access_token: string; token_type: string }>(
    '/auth/login',
    body,
  )
  return data
}

export async function register(body: RegisterBody) {
  const { data } = await apiClient.post<User>('/auth/register', body)
  return data
}

export async function verifyEmail(token: string) {
  const { data } = await apiClient.post<User>('/auth/verify-email', { token })
  return data
}

export async function forgotPassword(email: string) {
  await apiClient.post('/auth/forgot-password', { email })
}

export async function resetPassword(body: ResetPasswordBody) {
  await apiClient.post('/auth/reset-password', body)
}

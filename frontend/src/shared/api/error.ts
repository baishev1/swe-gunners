import { isAxiosError } from 'axios'

export function getErrorMessage(error: unknown) {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return 'Something went wrong. Try again.'
}

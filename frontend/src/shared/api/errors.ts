import { isAxiosError } from 'axios'

export function getErrorMessage(error: unknown) {
  if (isAxiosError(error) && typeof error.response?.data?.detail === 'string') {
    return error.response.data.detail
  }
  return 'Something went wrong'
}

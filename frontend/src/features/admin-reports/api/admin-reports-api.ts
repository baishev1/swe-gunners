import { useMutation } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

export type ReportKind = 'orders' | 'payments' | 'events' | 'users'

export interface ReportRequest {
  report: ReportKind
  dateFrom: string | null
  dateTo: string | null
}

function filenameFrom(disposition: unknown, fallback: string) {
  if (typeof disposition !== 'string') return fallback
  return /filename="([^"]+)"/.exec(disposition)?.[1] ?? fallback
}

/** Downloads through the API client so the bearer token is sent, then saves the CSV. */
export function useExportReport() {
  return useMutation({
    mutationFn: async ({ report, dateFrom, dateTo }: ReportRequest) => {
      const response = await apiClient.get<Blob>('/admin/reports/export', {
        params: { report, date_from: dateFrom ?? undefined, date_to: dateTo ?? undefined },
        responseType: 'blob',
      })
      const url = URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url
      link.download = filenameFrom(response.headers['content-disposition'], `${report}.csv`)
      link.click()
      URL.revokeObjectURL(url)
    },
  })
}

import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import type { ResolvedPromo } from '@/entities/promo-campaign'
import { apiClient } from '@/shared/api'

const storageKey = (eventId: string) => `promo:${eventId}`

function isResolvedPromo(value: unknown): value is ResolvedPromo {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as ResolvedPromo).code === 'string' &&
    Array.isArray((value as ResolvedPromo).ticket_type_ids)
  )
}

/** The promo a Campaign QR link applied to this event in the current tab, if any. */
export function getAppliedPromo(eventId: string): ResolvedPromo | null {
  try {
    const parsed: unknown = JSON.parse(sessionStorage.getItem(storageKey(eventId)) ?? 'null')
    return isResolvedPromo(parsed) ? parsed : null
  } catch {
    return null
  }
}

export function clearAppliedPromo(eventId: string) {
  try {
    sessionStorage.removeItem(storageKey(eventId))
  } catch {
    // Nothing stored, nothing to clear.
  }
}

function rememberPromo(promo: ResolvedPromo) {
  try {
    sessionStorage.setItem(storageKey(promo.event_id), JSON.stringify(promo))
  } catch {
    // The banner still shows the code; checkout just will not apply it.
  }
}

export function usePromoLink() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('promo') ?? ''

  return useQuery({
    queryKey: ['promo-link', token],
    queryFn: async () => {
      const promo = (await apiClient.get<ResolvedPromo>('/promo/resolve', { params: { token } }))
        .data
      rememberPromo(promo)
      return promo
    },
    enabled: Boolean(token),
    retry: false,
  })
}

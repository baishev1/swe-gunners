import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import type { ResolvedPromo } from '@/entities/promo-campaign'
import { apiClient } from '@/shared/api'

const storageKey = (eventId: string) => `promo_code:${eventId}`

export function getAppliedPromoCode(eventId: string) {
  try {
    return sessionStorage.getItem(storageKey(eventId))
  } catch {
    return null
  }
}

function rememberPromoCode(promo: ResolvedPromo) {
  try {
    sessionStorage.setItem(storageKey(promo.event_id), promo.code)
  } catch {
    // The banner still shows the code; checkout just will not prefill it.
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
      rememberPromoCode(promo)
      return promo
    },
    enabled: Boolean(token),
    retry: false,
  })
}

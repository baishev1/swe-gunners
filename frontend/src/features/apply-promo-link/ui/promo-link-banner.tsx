import { isAxiosError } from 'axios'
import { useTranslation } from 'react-i18next'

import { formatDiscount } from '@/entities/promo-campaign'

import { usePromoLink } from '../model/use-promo-link'

export function PromoLinkBanner({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const promo = usePromoLink()

  if (promo.isError) {
    return (
      <p role="alert" className="text-destructive text-sm">
        {isAxiosError(promo.error) && promo.error.response?.status === 404
          ? t('promoLink.invalid')
          : t('promoLink.unavailable')}
      </p>
    )
  }
  if (!promo.data || promo.data.event_id !== eventId) return null

  return (
    <p role="status" className="bg-muted rounded-md px-3 py-2 text-sm">
      {t('promoLink.applied', {
        code: promo.data.code,
        discount: formatDiscount(promo.data.discount_type, promo.data.discount_value),
      })}
    </p>
  )
}

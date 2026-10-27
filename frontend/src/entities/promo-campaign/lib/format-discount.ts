import { formatPrice } from '@/shared/lib/format'

import type { DiscountType } from '../model/types'

export function formatDiscount(discountType: DiscountType, discountValue: number) {
  return discountType === 'percent' ? `−${discountValue}%` : `−${formatPrice(discountValue)}`
}

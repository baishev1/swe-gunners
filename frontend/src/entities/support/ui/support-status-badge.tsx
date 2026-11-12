import { useTranslation } from 'react-i18next'

import { Badge } from '@/shared/ui/badge'
import type { SupportStatus } from '../model/types'

const VARIANTS = {
  open: 'warning',
  in_progress: 'default',
  waiting_for_customer: 'secondary',
  resolved: 'success',
} as const

export function SupportStatusBadge({ status }: { status: SupportStatus }) {
  const { t } = useTranslation()

  return <Badge variant={VARIANTS[status]}>{t(`support.statuses.${status}`)}</Badge>
}

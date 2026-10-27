import { useTranslation } from 'react-i18next'

import { type PromoCampaign, useCampaignQr } from '@/entities/promo-campaign'
import { getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'

export function CampaignQr({ campaign }: { campaign: PromoCampaign }) {
  const { t } = useTranslation()
  const qr = useCampaignQr(campaign.id)

  if (qr.isPending) return <Skeleton className="size-48" />
  if (qr.isError) {
    return <p className="text-destructive text-sm">{getErrorMessage(qr.error)}</p>
  }

  const src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(qr.data)}`

  return (
    <div className="flex flex-col items-start gap-3">
      <img src={src} alt={t('promoCampaigns.qrAlt', { code: campaign.code })} className="size-48" />
      <Button variant="outline" size="sm" asChild>
        <a href={src} download={`campaign-${campaign.code}.svg`}>
          {t('promoCampaigns.downloadQr')}
        </a>
      </Button>
    </div>
  )
}

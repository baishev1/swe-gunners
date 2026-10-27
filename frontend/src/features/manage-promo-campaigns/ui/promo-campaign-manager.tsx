import { useTranslation } from 'react-i18next'
import { useState } from 'react'

import { formatDiscount, usePromoCampaigns } from '@/entities/promo-campaign'
import { getErrorMessage } from '@/shared/api'
import { formatDateTime } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/shared/ui/card'
import { FieldError } from '@/shared/ui/field'

import { useDisablePromoCampaign } from '../model/use-promo-campaign-mutations'
import { CampaignQr } from './campaign-qr'
import { PromoCampaignForm } from './promo-campaign-form'

export function PromoCampaignManager({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const campaigns = usePromoCampaigns(eventId)
  const disableCampaign = useDisablePromoCampaign()
  const [openQrId, setOpenQrId] = useState<string | null>(null)

  return (
    <div className="flex flex-col gap-6">
      {campaigns.isError && <FieldError>{getErrorMessage(campaigns.error)}</FieldError>}
      {campaigns.data?.length === 0 && (
        <p className="text-muted-foreground text-sm">{t('promoCampaigns.empty')}</p>
      )}
      {campaigns.data?.map((campaign) => (
        <Card key={campaign.id}>
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center gap-2">
              {campaign.name}
              <Badge variant="secondary" className="font-mono">
                {campaign.code}
              </Badge>
            </CardTitle>
            <CardDescription>
              {formatDiscount(campaign.discount_type, campaign.discount_value)} ·{' '}
              {t('promoCampaigns.redemptions', {
                used: campaign.redemption_count,
                limit: campaign.max_redemptions ?? '∞',
              })}
              {campaign.end_time &&
                ` · ${t('promoCampaigns.until', { date: formatDateTime(campaign.end_time) })}`}
            </CardDescription>
            <CardAction className="flex items-center gap-2">
              {campaign.is_disabled ? (
                <Badge variant="outline">{t('promoCampaigns.disabled')}</Badge>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={disableCampaign.isPending}
                  onClick={() => disableCampaign.mutate(campaign.id)}
                >
                  {t('promoCampaigns.disable')}
                </Button>
              )}
            </CardAction>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {campaign.ticket_type_ids.length > 0 && (
              <p className="text-muted-foreground text-sm">
                {t('promoCampaigns.limitedTo', { n: campaign.ticket_type_ids.length })}
              </p>
            )}
            {openQrId === campaign.id ? (
              <CampaignQr campaign={campaign} />
            ) : (
              <Button
                variant="link"
                className="self-start px-0"
                onClick={() => setOpenQrId(campaign.id)}
              >
                {t('promoCampaigns.showQr')}
              </Button>
            )}
          </CardContent>
        </Card>
      ))}
      {disableCampaign.isError && <FieldError>{getErrorMessage(disableCampaign.error)}</FieldError>}
      <Card>
        <CardHeader>
          <CardTitle>{t('promoCampaigns.newCampaign')}</CardTitle>
        </CardHeader>
        <CardContent>
          <PromoCampaignForm eventId={eventId} />
        </CardContent>
      </Card>
    </div>
  )
}

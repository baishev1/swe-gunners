import { useTranslation } from 'react-i18next'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'

import { formatDiscount } from '@/entities/promo-campaign'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'

import { useAdminPromoCampaigns } from '../api/admin-promo-campaigns-api'

export function AdminPromoCampaignsPanel() {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const campaigns = useAdminPromoCampaigns(search)

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSearch(query.trim())
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSubmit} className="flex flex-wrap gap-2">
        <Input
          aria-label={t('admin.searchCampaigns')}
          placeholder={t('admin.searchCampaigns')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="max-w-xs"
        />
        <Button type="submit" variant="outline">
          {t('admin.search')}
        </Button>
      </form>
      {campaigns.isError && <FieldError>{getErrorMessage(campaigns.error)}</FieldError>}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t('promoCampaigns.code')}</TableHead>
            <TableHead>{t('promoCampaigns.name')}</TableHead>
            <TableHead>{t('promoCampaigns.discount')}</TableHead>
            <TableHead className="text-right">{t('promoCampaigns.redemptionsColumn')}</TableHead>
            <TableHead>{t('admin.status')}</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {campaigns.data?.map((campaign) => (
            <TableRow key={campaign.id}>
              <TableCell className="font-mono">{campaign.code}</TableCell>
              <TableCell>{campaign.name}</TableCell>
              <TableCell>
                {formatDiscount(campaign.discount_type, campaign.discount_value)}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {campaign.redemption_count} / {campaign.max_redemptions ?? '∞'}
              </TableCell>
              <TableCell>
                <Badge variant={campaign.is_disabled ? 'outline' : 'secondary'}>
                  {campaign.is_disabled ? t('promoCampaigns.disabled') : t('admin.active')}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                <Button variant="link" size="sm" asChild>
                  <Link to={`${ROUTES.eventHistory}?event_id=${campaign.event_id}`}>
                    {t('admin.history')}
                  </Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {campaigns.data?.length === 0 && (
        <p className="text-muted-foreground text-sm">{t('admin.nothingFound')}</p>
      )}
    </div>
  )
}

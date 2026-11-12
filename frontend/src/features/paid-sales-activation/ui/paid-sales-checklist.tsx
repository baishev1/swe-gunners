import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { type PaidSalesStatus, usePaidSalesChecklist } from '@/entities/paid-sales'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatPrice } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { FieldError } from '@/shared/ui/field'
import { Skeleton } from '@/shared/ui/skeleton'

import { usePaidSalesStep, useVerifyIdentity } from '../model/use-paid-sales-mutations'

const STATUS_VARIANT: Record<PaidSalesStatus, 'secondary' | 'default' | 'destructive'> = {
  pending: 'secondary',
  active: 'default',
  suspended: 'destructive',
}

function ChecklistItem({
  done,
  label,
  action,
}: {
  done: boolean
  label: string
  action?: ReactNode
}) {
  const { t } = useTranslation()
  return (
    <li className="flex flex-wrap items-center justify-between gap-2 border-b py-3 last:border-0">
      <span className="flex items-center gap-2 text-sm">
        <span aria-hidden className={done ? 'text-primary' : 'text-muted-foreground'}>
          {done ? '✓' : '○'}
        </span>
        <span>{label}</span>
        <span className="sr-only">{done ? t('paidSales.stepDone') : t('paidSales.stepTodo')}</span>
      </span>
      {!done && action}
    </li>
  )
}

export function PaidSalesChecklistCard({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const checklist = usePaidSalesChecklist(eventId)
  const step = usePaidSalesStep(eventId)
  const verifyIdentity = useVerifyIdentity()

  if (checklist.isPending) return <Skeleton className="h-48 w-full" />
  if (checklist.isError) return <FieldError>{getErrorMessage(checklist.error)}</FieldError>

  const data = checklist.data
  const locked = data.status !== 'pending'
  const busy = step.isPending || verifyIdentity.isPending

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <CardTitle>{t('paidSales.title')}</CardTitle>
          <Badge variant={STATUS_VARIANT[data.status]}>
            {t(`paidSales.statuses.${data.status}`)}
          </Badge>
        </div>
        <CardDescription>{t('paidSales.description')}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {data.status === 'active' && <p className="text-sm">{t('paidSales.activeNotice')}</p>}
        {data.status === 'suspended' && (
          <p className="text-destructive text-sm">
            {t('paidSales.suspendedNotice', { reason: data.suspension_reason ?? '' })}
          </p>
        )}
        <ul aria-label={t('paidSales.checklist')}>
          <ChecklistItem done={data.has_paid_ticket_type} label={t('paidSales.paidTicketType')} />
          <ChecklistItem
            done={data.identity_verified}
            label={t('paidSales.identity')}
            action={
              <Button
                size="sm"
                variant="outline"
                disabled={busy}
                onClick={() => verifyIdentity.mutate()}
              >
                {t('paidSales.verifyIdentity')}
              </Button>
            }
          />
          <ChecklistItem
            done={data.payout_account_ready}
            label={t('paidSales.payoutAccount')}
            action={
              <Button size="sm" variant="outline" asChild>
                <Link to={ROUTES.organizerProfile}>{t('paidSales.addPayout')}</Link>
              </Button>
            }
          />
          <ChecklistItem
            done={data.fee_paid}
            label={t('paidSales.fee', { fee: formatPrice(data.fee_amount) })}
            action={
              !locked && (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => step.mutate('pay-fee')}
                >
                  {t('paidSales.payFee')}
                </Button>
              )
            }
          />
          <ChecklistItem
            done={data.terms_accepted}
            label={t('paidSales.terms')}
            action={
              !locked && (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => step.mutate('accept-terms')}
                >
                  {t('paidSales.acceptTerms')}
                </Button>
              )
            }
          />
        </ul>
        <p className="text-muted-foreground text-xs">{t('paidSales.simulationNotice')}</p>
        {data.status === 'pending' && (
          <Button
            className="self-start"
            disabled={!data.can_activate || busy}
            onClick={() => step.mutate('activate')}
          >
            {t('paidSales.activate')}
          </Button>
        )}
        {step.isError && <FieldError>{getErrorMessage(step.error)}</FieldError>}
        {verifyIdentity.isError && <FieldError>{getErrorMessage(verifyIdentity.error)}</FieldError>}
      </CardContent>
    </Card>
  )
}

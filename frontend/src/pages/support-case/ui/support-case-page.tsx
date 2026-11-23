import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { SupportStatusBadge, useSupportCase, useSupportMessages } from '@/entities/support'
import { useMe } from '@/entities/session'
import { SupportCaseActions } from '@/features/manage-support-case'
import { SupportReplyForm, SupportThread } from '@/features/support-chat'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDateTime, formatPrice } from '@/shared/lib/format'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'

export function SupportCasePage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const caseId = searchParams.get('case_id') ?? ''
  const { data: me } = useMe()
  const supportCase = useSupportCase(caseId)
  const messages = useSupportMessages(caseId)

  if (supportCase.isPending) {
    return (
      <main className="mx-auto max-w-2xl p-6">
        <Skeleton className="h-64 w-full" />
      </main>
    )
  }

  if (supportCase.isError) {
    return (
      <main className="mx-auto flex max-w-2xl flex-col gap-4 p-6">
        <p className="text-destructive text-sm">{getErrorMessage(supportCase.error)}</p>
        <Link to={ROUTES.support} className="text-sm underline">
          {t('support.backToCases')}
        </Link>
      </main>
    )
  }

  const data = supportCase.data

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <div className="flex flex-col gap-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <SupportStatusBadge status={data.status} />
          <span className="text-muted-foreground text-xs">
            {t('support.caseUpdated', { date: formatDateTime(data.updated_at) })}
          </span>
        </div>
        <h1 className="text-2xl font-semibold">{data.subject}</h1>
        <p className="text-muted-foreground text-sm">{t(`support.categories.${data.category}`)}</p>
        {(data.order_id || data.ticket_id) && (
          <dl className="text-muted-foreground grid gap-1 text-sm">
            {data.order_id && (
              <div>
                <dt className="sr-only">{t('support.context.orderLabel')}</dt>
                <dd>
                  {t('support.context.order', { number: data.order_id.slice(0, 8) })}
                  {data.order_status &&
                    ` · ${t(`organizerOrders.statuses.${data.order_status}`, { defaultValue: data.order_status })}`}
                  {data.order_total_kzt != null && ` · ${formatPrice(data.order_total_kzt)}`}
                </dd>
              </div>
            )}
            {data.ticket_id && (
              <div>
                <dt className="sr-only">{t('support.context.ticketLabel')}</dt>
                <dd>
                  {t('support.context.ticket', { number: data.ticket_id.slice(0, 8) })}
                  {data.ticket_type_name && ` · ${data.ticket_type_name}`}
                  {data.ticket_status &&
                    ` · ${t(`eventAttendees.statuses.${data.ticket_status}`, { defaultValue: data.ticket_status })}`}
                </dd>
              </div>
            )}
          </dl>
        )}
        {data.event_id && (
          <Link
            to={`${ROUTES.eventDetail}?event_id=${data.event_id}`}
            className="w-fit text-sm underline"
          >
            {t('support.viewEvent')}
          </Link>
        )}
      </div>

      <SupportCaseActions supportCase={data} />

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">{t('support.thread.title')}</h2>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          {messages.isPending && <Skeleton className="h-32 w-full" />}
          {messages.isError && (
            <p className="text-destructive text-sm">{getErrorMessage(messages.error)}</p>
          )}
          {messages.data && me && <SupportThread messages={messages.data} currentUserId={me.id} />}
          {me && <SupportReplyForm caseId={data.id} />}
        </CardContent>
      </Card>

      <Link to={ROUTES.support} className="text-sm underline">
        {t('support.backToCases')}
      </Link>
    </main>
  )
}

import { useTranslation } from 'react-i18next'
import { Link, useSearchParams } from 'react-router-dom'

import { SUPPORT_CATEGORIES, type SupportCategory } from '@/entities/support'
import { SupportCaseForm } from '@/features/contact-support'
import { ROUTES } from '@/shared/config'

function isSupportCategory(value: string | null): value is SupportCategory {
  return SUPPORT_CATEGORIES.some((category) => category === value)
}

export function SupportNewPage() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const eventId = searchParams.get('event_id') ?? undefined
  const orderId = searchParams.get('order_id') ?? undefined
  const ticketId = searchParams.get('ticket_id') ?? undefined
  const category = searchParams.get('category')

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold">{t('support.form.pageTitle')}</h1>
        <p className="text-muted-foreground text-sm">{t('support.form.pageDescription')}</p>
      </div>
      <SupportCaseForm
        eventId={eventId}
        orderId={orderId}
        ticketId={ticketId}
        defaultCategory={isSupportCategory(category) ? category : undefined}
      />
      <Link to={ROUTES.support} className="text-sm underline">
        {t('support.backToCases')}
      </Link>
    </main>
  )
}

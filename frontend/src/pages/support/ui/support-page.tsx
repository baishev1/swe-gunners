import { Plus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

import { SupportStatusBadge, useSupportCases } from '@/entities/support'
import { useMe } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDateTime } from '@/shared/lib/format'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'

export function SupportPage() {
  const { t } = useTranslation()
  const { data: me } = useMe()
  const { data: cases, isPending, isError, error } = useSupportCases()
  const canCreateRequest = me?.role === 'organizer' || me?.role === 'platform_admin'

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold">{t('support.title')}</h1>
          <p className="text-muted-foreground text-sm">{t('support.description')}</p>
        </div>
        {canCreateRequest ? (
          <Button asChild size="sm">
            <Link to={ROUTES.supportNew}>
              <Plus />
              {t('support.newRequest')}
            </Link>
          </Button>
        ) : null}
      </div>

      <p className="text-muted-foreground text-sm">{t('support.openFromPage')}</p>

      {isPending && (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}
      {isError && <p className="text-destructive text-sm">{getErrorMessage(error)}</p>}
      {cases?.length === 0 && (
        <Card>
          <CardContent className="text-muted-foreground py-8 text-center text-sm">
            {t('support.empty')}
          </CardContent>
        </Card>
      )}
      <div className="flex flex-col gap-3">
        {cases?.map((supportCase) => (
          <Link key={supportCase.id} to={`${ROUTES.supportCase}?case_id=${supportCase.id}`}>
            <Card className="transition-colors hover:border-foreground/20">
              <CardHeader className="flex flex-row items-start justify-between gap-4">
                <CardTitle className="text-base">{supportCase.subject}</CardTitle>
                <SupportStatusBadge status={supportCase.status} />
              </CardHeader>
              <CardContent className="flex flex-wrap justify-between gap-2 text-sm">
                <span>{t(`support.categories.${supportCase.category}`)}</span>
                <span className="text-muted-foreground">
                  {formatDateTime(supportCase.updated_at)}
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <Link to={ROUTES.home} className="text-sm underline">
        {t('common.backToHome')}
      </Link>
    </main>
  )
}

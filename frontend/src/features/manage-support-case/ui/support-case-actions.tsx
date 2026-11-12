import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import {
  assignSupportCase,
  supportKeys,
  updateSupportStatus,
  type SupportCase,
  type SupportStatus,
} from '@/entities/support'
import { useMe } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { FieldError } from '@/shared/ui/field'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'

const STATUSES: SupportStatus[] = ['open', 'in_progress', 'waiting_for_customer', 'resolved']

export function SupportCaseActions({ supportCase }: { supportCase: SupportCase }) {
  const { t } = useTranslation()
  const { data: me } = useMe()
  const queryClient = useQueryClient()

  const canManage =
    me?.role === 'platform_admin' ||
    (me?.role === 'organizer' && supportCase.target === 'organizer')

  const refresh = (updated: SupportCase) => {
    queryClient.setQueryData(supportKeys.case(updated.id), updated)
    void queryClient.invalidateQueries({ queryKey: supportKeys.cases() })
  }

  const statusMutation = useMutation({
    mutationFn: (status: SupportStatus) => updateSupportStatus(supportCase.id, status),
    onSuccess: refresh,
  })

  const assignMutation = useMutation({
    mutationFn: () => assignSupportCase(supportCase.id),
    onSuccess: refresh,
  })

  if (!canManage) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('support.manage.title')}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-sm">{t('support.manage.status')}</span>
          <NativeSelect
            value={supportCase.status}
            disabled={statusMutation.isPending}
            onChange={(event) => statusMutation.mutate(event.target.value as SupportStatus)}
          >
            {STATUSES.map((status) => (
              <NativeSelectOption key={status} value={status}>
                {t(`support.statuses.${status}`)}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-sm">
            {supportCase.assignee_id === null
              ? t('support.manage.unassigned')
              : supportCase.assignee_id === me?.id
                ? t('support.manage.assignedToYou')
                : t('support.manage.assignedToStaff')}
          </span>
          {supportCase.assignee_id !== me?.id && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => assignMutation.mutate()}
              disabled={assignMutation.isPending}
            >
              {t('support.manage.assignToMe')}
            </Button>
          )}
        </div>
        {statusMutation.isError && <FieldError>{getErrorMessage(statusMutation.error)}</FieldError>}
        {assignMutation.isError && <FieldError>{getErrorMessage(assignMutation.error)}</FieldError>}
      </CardContent>
    </Card>
  )
}

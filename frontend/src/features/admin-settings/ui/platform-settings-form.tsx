import { useTranslation } from 'react-i18next'
import { type FormEvent, useState } from 'react'

import { getErrorMessage } from '@/shared/api'
import { formatPrice } from '@/shared/lib/format'
import { Button } from '@/shared/ui/button'
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { Skeleton } from '@/shared/ui/skeleton'

import {
  type PlatformSettings,
  usePlatformSettings,
  useUpdatePlatformSettings,
} from '../api/platform-settings-api'

export function PlatformSettingsForm() {
  const settings = usePlatformSettings()

  if (settings.isPending) return <Skeleton className="h-32 w-full" />
  if (settings.isError) return <FieldError>{getErrorMessage(settings.error)}</FieldError>

  return <ActivationFeeForm key={settings.data.updated_at} settings={settings.data} />
}

function ActivationFeeForm({ settings }: { settings: PlatformSettings }) {
  const { t } = useTranslation()
  const updateSettings = useUpdatePlatformSettings()
  const [fee, setFee] = useState(String(settings.activation_fee / 100))

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    updateSettings.mutate({ activation_fee: Math.round(Number(fee) * 100) })
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-sm">
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="activation-fee">{t('admin.activationFee')}</FieldLabel>
          <Input
            id="activation-fee"
            type="number"
            min={0}
            step="0.01"
            required
            value={fee}
            onChange={(e) => setFee(e.target.value)}
          />
          <FieldDescription>
            {t('admin.activationFeeCurrent', { fee: formatPrice(settings.activation_fee) })}
          </FieldDescription>
        </Field>
        {updateSettings.isError && <FieldError>{getErrorMessage(updateSettings.error)}</FieldError>}
        {updateSettings.isSuccess && (
          <p className="text-muted-foreground text-sm">{t('admin.saved')}</p>
        )}
        <Button type="submit" disabled={updateSettings.isPending}>
          {t('admin.save')}
        </Button>
      </FieldGroup>
    </form>
  )
}

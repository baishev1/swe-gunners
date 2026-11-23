import { isAxiosError } from 'axios'
import { type KeyboardEvent, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Button, Input } from '@/shared/ui'

interface PromoCodeFieldProps {
  /** Validates the code on the server and applies it; throws when it is rejected. */
  onApply: (code: string) => Promise<void>
  disabled?: boolean
}

// API details are English, so the known rejections map to locale keys (SRS 4.14).
function promoErrorKey(error: unknown) {
  const status = isAxiosError(error) ? error.response?.status : undefined
  if (status === 404 || status === 422) return 'checkout.promoCode.invalid'
  if (status === 400) return 'promoLink.unavailable'
  return 'checkout.errors.generic'
}

/** Typed promo code, the counterpart of a Campaign QR link. */
export function PromoCodeField({ onApply, disabled }: PromoCodeFieldProps) {
  const { t } = useTranslation()
  const [code, setCode] = useState('')
  const [isApplying, setIsApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function apply() {
    const value = code.trim()
    if (!value) return
    setError(null)
    setIsApplying(true)
    try {
      await onApply(value)
      setCode('')
    } catch (err: unknown) {
      setError(t(promoErrorKey(err)))
    } finally {
      setIsApplying(false)
    }
  }

  // The field sits inside the checkout form: Enter applies the code instead of ordering.
  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      void apply()
    }
  }

  return (
    <div className="space-y-1 border-t pt-3">
      <label htmlFor="promo-code" className="text-xs font-medium text-muted-foreground">
        {t('checkout.promoCode.label')}
      </label>
      <div className="flex gap-2">
        <Input
          id="promo-code"
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          maxLength={20}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isApplying}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? 'promo-code-error' : undefined}
        />
        <Button
          type="button"
          variant="outline"
          onClick={() => void apply()}
          disabled={disabled || isApplying || !code.trim()}
        >
          {t('checkout.promoCode.apply')}
        </Button>
      </div>
      {error && (
        <p id="promo-code-error" role="alert" className="text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}

import { i18n } from '@/shared/i18n'

export function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString(i18n.language, { dateStyle: 'medium', timeStyle: 'short' })
}

export function formatPrice(minorUnits: number) {
  if (minorUnits === 0) return i18n.t('common.free')
  return (minorUnits / 100).toLocaleString(i18n.language, { style: 'currency', currency: 'KZT' })
}

export function toDateTimeInput(iso: string | null) {
  if (!iso) return ''
  const date = new Date(iso)
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

export function fromDateTimeInput(value: string) {
  return value ? new Date(value).toISOString() : null
}

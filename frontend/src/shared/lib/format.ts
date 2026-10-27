export function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('ru-KZ', { dateStyle: 'medium', timeStyle: 'short' })
}

export function formatPrice(minorUnits: number) {
  if (minorUnits === 0) return 'Free'
  return (minorUnits / 100).toLocaleString('ru-KZ', { style: 'currency', currency: 'KZT' })
}

export function toDateTimeInput(iso: string | null) {
  if (!iso) return ''
  const date = new Date(iso)
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

export function fromDateTimeInput(value: string) {
  return value ? new Date(value).toISOString() : null
}

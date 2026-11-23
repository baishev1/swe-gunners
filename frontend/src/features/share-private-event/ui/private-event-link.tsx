import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { apiClient } from '@/shared/api'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Skeleton } from '@/shared/ui/skeleton'

/** The secret link that opens a private event to guests (SRS 4.2). */
export function PrivateEventLink({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)
  const link = useQuery({
    queryKey: ['event-access-link', eventId],
    queryFn: async () =>
      (
        await apiClient.get<{ link: string }>('/events/access-link', {
          params: { event_id: eventId },
        })
      ).data.link,
  })

  async function copy() {
    if (!link.data) return
    try {
      await navigator.clipboard.writeText(link.data)
      setCopied(true)
    } catch {
      // Clipboard can be blocked; the field stays selectable for a manual copy.
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('privateLink.title')}</CardTitle>
        <CardDescription>{t('privateLink.description')}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-2 sm:flex-row">
        {link.data ? (
          <>
            <Input
              readOnly
              value={link.data}
              aria-label={t('privateLink.title')}
              onFocus={(e) => e.currentTarget.select()}
            />
            <Button type="button" variant="outline" onClick={copy}>
              {copied ? t('privateLink.copied') : t('privateLink.copy')}
            </Button>
          </>
        ) : (
          <Skeleton className="h-10 w-full" />
        )}
      </CardContent>
    </Card>
  )
}

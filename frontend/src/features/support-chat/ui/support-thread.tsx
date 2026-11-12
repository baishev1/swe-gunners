import { useTranslation } from 'react-i18next'

import type { SupportMessage } from '@/entities/support'
import { cn } from '@/shared/lib/utils'
import { formatDateTime } from '@/shared/lib/format'

interface SupportThreadProps {
  messages: SupportMessage[]
  currentUserId: string
}

export function SupportThread({ messages, currentUserId }: SupportThreadProps) {
  const { t } = useTranslation()

  if (messages.length === 0) {
    return <p className="text-muted-foreground text-sm">{t('support.thread.empty')}</p>
  }

  return (
    <div className="flex flex-col gap-4">
      {messages.map((message) => {
        const own = message.author_id === currentUserId
        return (
          <div
            key={message.id}
            className={cn(
              'flex max-w-[85%] flex-col gap-1',
              own ? 'self-end items-end' : 'self-start',
            )}
          >
            <p className="text-muted-foreground text-xs">
              {own ? t('support.thread.you') : t('support.thread.participant')}
            </p>
            <div
              className={cn(
                'rounded-lg px-4 py-3 text-sm whitespace-pre-line',
                own ? 'bg-primary text-primary-foreground' : 'bg-muted',
              )}
            >
              {message.body}
            </div>
            <p className="text-muted-foreground text-xs">{formatDateTime(message.created_at)}</p>
          </div>
        )
      })}
    </div>
  )
}

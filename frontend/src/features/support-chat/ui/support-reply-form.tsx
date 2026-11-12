import { useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { addSupportMessage, supportKeys } from '@/entities/support'
import { getErrorMessage } from '@/shared/api'
import { useTranslation } from 'react-i18next'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'
import { Textarea } from '@/shared/ui/textarea'

export function SupportReplyForm({ caseId }: { caseId: string }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [body, setBody] = useState('')

  const mutation = useMutation({
    mutationFn: (message: string) => addSupportMessage(caseId, message),
    onSuccess: () => {
      setBody('')
      void queryClient.invalidateQueries({ queryKey: supportKeys.messages(caseId) })
      void queryClient.invalidateQueries({ queryKey: supportKeys.case(caseId) })
      void queryClient.invalidateQueries({ queryKey: supportKeys.cases() })
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = body.trim()
    if (trimmed) mutation.mutate(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <Textarea
        value={body}
        onChange={(event) => setBody(event.target.value)}
        placeholder={t('support.thread.replyPlaceholder')}
        rows={3}
        maxLength={5000}
        required
      />
      {mutation.isError && <FieldError>{getErrorMessage(mutation.error)}</FieldError>}
      <Button type="submit" disabled={mutation.isPending || !body.trim()} className="self-end">
        {mutation.isPending ? t('support.thread.sending') : t('support.thread.send')}
      </Button>
    </form>
  )
}

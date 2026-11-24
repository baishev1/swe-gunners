import { type FormEvent, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Field, FieldError, FieldGroup, FieldLabel } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { Skeleton } from '@/shared/ui/skeleton'

import {
  staffErrorKey,
  useAssignStaff,
  useEventStaff,
  useRemoveStaff,
} from '../model/use-event-staff'

/** Assigns Event Admins who check attendees in with the mobile app (SRS 1.2, 2.3, 4.8). */
export function EventStaffManager({ eventId }: { eventId: string }) {
  const { t } = useTranslation()
  const staff = useEventStaff(eventId)
  const assign = useAssignStaff(eventId)
  const remove = useRemoveStaff(eventId)
  const [email, setEmail] = useState('')
  const [canUndo, setCanUndo] = useState(true)
  const [canSupport, setCanSupport] = useState(false)

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    assign.mutate(
      { email: email.trim(), can_undo_check_in: canUndo, can_manage_support: canSupport },
      { onSuccess: () => setEmail('') },
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <p className="text-muted-foreground text-sm">{t('eventStaff.description')}</p>

      {staff.isPending ? (
        <Skeleton className="h-16 w-full" />
      ) : staff.data?.length === 0 ? (
        <p className="text-muted-foreground text-sm">{t('eventStaff.empty')}</p>
      ) : (
        <ul className="flex flex-col divide-y rounded-md border">
          {staff.data?.map((member) => (
            <li key={member.id} className="flex items-center justify-between gap-3 p-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{member.user_full_name}</p>
                <p className="text-muted-foreground truncate text-xs">{member.user_email}</p>
                <p className="mt-1 text-xs font-medium uppercase tracking-wide">
                  {[
                    member.can_undo_check_in && t('eventStaff.undoBadge'),
                    member.can_manage_support && t('eventStaff.supportBadge'),
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => remove.mutate(member.id)}
                disabled={remove.isPending}
                aria-label={t('eventStaff.remove', { name: member.user_email })}
              >
                ✕
              </Button>
            </li>
          ))}
        </ul>
      )}
      {remove.isError && <FieldError>{t(staffErrorKey(remove.error))}</FieldError>}

      <form onSubmit={handleSubmit}>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="staff-email">{t('eventStaff.email')}</FieldLabel>
            <Input
              id="staff-email"
              type="email"
              autoComplete="off"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Field>
          <Field orientation="horizontal">
            <Checkbox
              id="staff-can-undo"
              checked={canUndo}
              onCheckedChange={(checked) => setCanUndo(checked === true)}
            />
            <FieldLabel htmlFor="staff-can-undo">{t('eventStaff.canUndo')}</FieldLabel>
          </Field>
          <Field orientation="horizontal">
            <Checkbox
              id="staff-can-support"
              checked={canSupport}
              onCheckedChange={(checked) => setCanSupport(checked === true)}
            />
            <FieldLabel htmlFor="staff-can-support">{t('eventStaff.canSupport')}</FieldLabel>
          </Field>
          {assign.isError && <FieldError>{t(staffErrorKey(assign.error))}</FieldError>}
          <Button type="submit" className="self-start" disabled={assign.isPending}>
            {t('eventStaff.add')}
          </Button>
        </FieldGroup>
      </form>
    </div>
  )
}

import { useTranslation } from 'react-i18next'
import { type FormEvent, useState } from 'react'

import { useMe } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { FieldError } from '@/shared/ui/field'
import { Input } from '@/shared/ui/input'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'

import { useAdminUsers, useSuspendUser } from '../api/admin-users-api'

const ROLES = ['attendee', 'organizer', 'event_admin', 'platform_admin'] as const

export function AdminUsersPanel() {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [role, setRole] = useState('')
  const users = useAdminUsers(search, role)
  const suspendUser = useSuspendUser()
  const { data: me } = useMe()

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setSearch(query.trim())
  }

  return (
    <div className="flex flex-col gap-4">
      <form onSubmit={handleSubmit} className="flex flex-wrap gap-2">
        <Input
          aria-label={t('admin.searchUsers')}
          placeholder={t('admin.searchUsers')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="max-w-xs"
        />
        <NativeSelect
          aria-label={t('admin.role')}
          value={role}
          onChange={(e) => setRole(e.target.value)}
        >
          <NativeSelectOption value="">{t('admin.allRoles')}</NativeSelectOption>
          {ROLES.map((value) => (
            <NativeSelectOption key={value} value={value}>
              {t(`admin.roles.${value}`)}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <Button type="submit" variant="outline">
          {t('admin.search')}
        </Button>
      </form>
      {users.isError && <FieldError>{getErrorMessage(users.error)}</FieldError>}
      {suspendUser.isError && <FieldError>{getErrorMessage(suspendUser.error)}</FieldError>}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t('admin.name')}</TableHead>
            <TableHead>{t('common.email')}</TableHead>
            <TableHead>{t('admin.role')}</TableHead>
            <TableHead>{t('admin.status')}</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {users.data?.map((user) => (
            <TableRow key={user.id}>
              <TableCell>{user.full_name}</TableCell>
              <TableCell>{user.email}</TableCell>
              <TableCell>{t(`admin.roles.${user.role}`)}</TableCell>
              <TableCell>
                {user.is_active ? (
                  <Badge variant="secondary">{t('admin.active')}</Badge>
                ) : (
                  <Badge variant="destructive">{t('admin.suspended')}</Badge>
                )}
              </TableCell>
              <TableCell className="text-right">
                {user.is_active && user.id !== me?.id && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={suspendUser.isPending}
                    onClick={() => suspendUser.mutate(user.id)}
                  >
                    {t('admin.suspend')}
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {users.data?.length === 0 && (
        <p className="text-muted-foreground text-sm">{t('admin.nothingFound')}</p>
      )}
    </div>
  )
}

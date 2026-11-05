import { useTranslation } from 'react-i18next'

import { AdminEventsPanel } from '@/features/admin-events'
import { AdminPaidSalesPanel } from '@/features/admin-paid-sales'
import { AdminPromoCampaignsPanel } from '@/features/admin-promo-campaigns'
import { PlatformSettingsForm } from '@/features/admin-settings'
import { AdminUsersPanel } from '@/features/admin-users'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'

export function AdminPage() {
  const { t } = useTranslation()

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 p-6">
      <h1 className="text-2xl font-semibold">{t('admin.title')}</h1>
      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">{t('admin.users')}</TabsTrigger>
          <TabsTrigger value="events">{t('admin.events')}</TabsTrigger>
          <TabsTrigger value="paid-sales">{t('admin.paidSales.tab')}</TabsTrigger>
          <TabsTrigger value="campaigns">{t('admin.campaigns')}</TabsTrigger>
          <TabsTrigger value="settings">{t('admin.settings')}</TabsTrigger>
        </TabsList>
        <TabsContent value="users">
          <AdminUsersPanel />
        </TabsContent>
        <TabsContent value="events">
          <AdminEventsPanel />
        </TabsContent>
        <TabsContent value="paid-sales">
          <AdminPaidSalesPanel />
        </TabsContent>
        <TabsContent value="campaigns">
          <AdminPromoCampaignsPanel />
        </TabsContent>
        <TabsContent value="settings">
          <PlatformSettingsForm />
        </TabsContent>
      </Tabs>
    </main>
  )
}

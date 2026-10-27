import { Route, Routes } from 'react-router-dom'

import { EventDetailPage } from '@/pages/event-detail'
import { EventsListPage } from '@/pages/events-list'
import { HomePage } from '@/pages/home'
import { NotFoundPage } from '@/pages/not-found'
import { OrganizerEventEditPage } from '@/pages/organizer-event-edit'
import { OrganizerEventNewPage } from '@/pages/organizer-event-new'
import { ROUTES } from '@/shared/config'

export function AppRouter() {
  return (
    <Routes>
      <Route path={ROUTES.home} element={<HomePage />} />
      <Route path={ROUTES.events} element={<EventsListPage />} />
      <Route path={ROUTES.eventDetail} element={<EventDetailPage />} />
      <Route path={ROUTES.organizerEventNew} element={<OrganizerEventNewPage />} />
      <Route path={ROUTES.organizerEventEdit} element={<OrganizerEventEditPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

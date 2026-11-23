export type EventStatus = 'draft' | 'published' | 'unpublished' | 'cancelled' | 'suspended'

export type EventVisibility = 'public' | 'unlisted' | 'private'

export interface EventPayload {
  title: string
  description: string | null
  category: string
  venue_id: string
  start_time: string
  end_time: string
  capacity: number
  visibility: EventVisibility
  registration_start_time: string | null
  registration_end_time: string | null
  cover_image_url: string | null
  refund_policy: string | null
}

export interface EventItem extends EventPayload {
  id: string
  organizer_id: string
  status: EventStatus
  timezone: string
  venue: { id: string; name: string; address: string }
  created_at: string
  updated_at: string
}

export type EventPhase = 'upcoming' | 'active' | 'completed' | 'cancelled'

export type OrganizerDashboard = Record<EventPhase, EventItem[]>

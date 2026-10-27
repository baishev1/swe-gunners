export type Role = 'attendee' | 'organizer' | 'event_admin' | 'platform_admin'

export type User = {
  id: string
  email: string
  full_name: string
  role: Role
  is_email_verified: boolean
}

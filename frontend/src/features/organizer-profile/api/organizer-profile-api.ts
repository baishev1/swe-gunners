import { apiClient } from '@/shared/api'

export type OrganizerProfile = {
  organization_name: string | null
  contact_email: string | null
  contact_phone: string | null
}

export async function fetchOrganizerProfile() {
  const { data } = await apiClient.get<OrganizerProfile>('/organizers/profile')
  return data
}

export async function updateOrganizerProfile(body: Partial<OrganizerProfile>) {
  const { data } = await apiClient.patch<OrganizerProfile>('/organizers/profile', body)
  return data
}

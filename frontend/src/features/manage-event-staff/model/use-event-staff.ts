import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { isAxiosError } from 'axios'

import { apiClient } from '@/shared/api'

export interface StaffAssignment {
  id: string
  event_id: string
  user_id: string
  user_email: string
  user_full_name: string
  can_undo_check_in: boolean
  can_manage_support: boolean
  created_at: string
}

export interface StaffAssignmentPayload {
  email: string
  can_undo_check_in: boolean
  can_manage_support: boolean
}

const staffKeys = {
  event: (eventId: string) => ['event-staff', eventId] as const,
}

export function useEventStaff(eventId: string) {
  return useQuery({
    queryKey: staffKeys.event(eventId),
    queryFn: async () =>
      (
        await apiClient.get<StaffAssignment[]>('/checkin/staff', {
          params: { event_id: eventId, limit: 100 },
        })
      ).data,
  })
}

export function useAssignStaff(eventId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: StaffAssignmentPayload) =>
      (
        await apiClient.post<StaffAssignment>('/checkin/staff', payload, {
          params: { event_id: eventId },
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: staffKeys.event(eventId) }),
  })
}

export function useRemoveStaff(eventId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (assignmentId: string) => {
      await apiClient.delete('/checkin/staff', {
        params: { event_id: eventId, assignment_id: assignmentId },
      })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: staffKeys.event(eventId) }),
  })
}

/** API error details are English, so the UI maps the known cases to locale keys. */
export function staffErrorKey(error: unknown) {
  const status = isAxiosError(error) ? error.response?.status : undefined
  if (status === 404) return 'eventStaff.errors.notFound'
  if (status === 409) return 'eventStaff.errors.duplicate'
  if (status === 400) return 'eventStaff.errors.invalid'
  return 'eventStaff.errors.generic'
}

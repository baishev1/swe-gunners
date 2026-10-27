export interface AuditEntry {
  id: string
  event_id: string | null
  actor_id: string | null
  actor_name: string | null
  action: string
  entity_type: string
  entity_id: string
  description: string
  created_at: string
}

export interface TimelineFilters {
  action: string
  dateFrom: string | null
  dateTo: string | null
}

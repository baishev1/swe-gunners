import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/shared/api'

import type { SupportCase, SupportCaseCreate, SupportMessage, SupportStatus } from '../model/types'

export const supportKeys = {
  all: ['support'] as const,
  cases: () => [...supportKeys.all, 'cases'] as const,
  case: (caseId: string) => [...supportKeys.all, 'case', caseId] as const,
  messages: (caseId: string) => [...supportKeys.all, 'messages', caseId] as const,
}

export async function createSupportCase(data: SupportCaseCreate) {
  return (await apiClient.post<SupportCase>('/support/cases', data)).data
}

export async function getSupportCase(caseId: string) {
  return (
    await apiClient.get<SupportCase>('/support/cases/detail', { params: { case_id: caseId } })
  ).data
}

export async function listSupportCases() {
  return (await apiClient.get<SupportCase[]>('/support/cases', { params: { limit: 100 } })).data
}

export async function listSupportMessages(caseId: string) {
  return (
    await apiClient.get<SupportMessage[]>('/support/messages', {
      params: { case_id: caseId, limit: 100 },
    })
  ).data
}

export async function addSupportMessage(caseId: string, body: string) {
  return (
    await apiClient.post<SupportMessage>(
      '/support/messages',
      { body },
      { params: { case_id: caseId } },
    )
  ).data
}

export async function updateSupportStatus(caseId: string, status: SupportStatus) {
  return (
    await apiClient.patch<SupportCase>(
      '/support/cases/status',
      { status },
      { params: { case_id: caseId } },
    )
  ).data
}

export async function assignSupportCase(caseId: string) {
  return (
    await apiClient.post<SupportCase>('/support/cases/assign', null, {
      params: { case_id: caseId },
    })
  ).data
}

export function useSupportCases() {
  return useQuery({ queryKey: supportKeys.cases(), queryFn: listSupportCases })
}

export function useSupportCase(caseId: string) {
  return useQuery({
    queryKey: supportKeys.case(caseId),
    queryFn: () => getSupportCase(caseId),
    enabled: Boolean(caseId),
  })
}

export function useSupportMessages(caseId: string) {
  return useQuery({
    queryKey: supportKeys.messages(caseId),
    queryFn: () => listSupportMessages(caseId),
    enabled: Boolean(caseId),
  })
}

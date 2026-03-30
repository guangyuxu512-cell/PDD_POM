import { api } from './index'
import type { Flow, FlowPayload, PaginatedList } from './types'

export function listFlows() {
  return api.get<PaginatedList<Flow>>('/api/flows')
}

export function createFlow(payload: FlowPayload) {
  return api.post<Flow>('/api/flows', payload)
}

export function updateFlow(flowId: string, payload: Partial<FlowPayload>) {
  return api.put<Flow>(`/api/flows/${flowId}`, payload)
}

export function deleteFlow(flowId: string) {
  return api.del<void>(`/api/flows/${flowId}`)
}

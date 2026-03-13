import { api } from './index'
import type {
  FlowParam,
  FlowParamBatchPayload,
  FlowParamFilters,
  FlowParamImportResult,
  FlowParamPayload,
  PaginatedList,
} from './types'

function buildQuery(filters: FlowParamFilters = {}) {
  const params = new URLSearchParams()

  if (filters.page) params.set('page', String(filters.page))
  if (filters.page_size) params.set('page_size', String(filters.page_size))
  if (filters.shop_id) params.set('shop_id', filters.shop_id)
  if (filters.flow_id) params.set('flow_id', filters.flow_id)
  if (filters.status) params.set('status', filters.status)
  if (filters.batch_id) params.set('batch_id', filters.batch_id)
  if (filters.sort_by) params.set('sort_by', filters.sort_by)
  if (filters.sort_order) params.set('sort_order', filters.sort_order)

  const query = params.toString()
  return query ? `?${query}` : ''
}

export function listFlowParams(filters: FlowParamFilters = {}) {
  return api.get<PaginatedList<FlowParam>>(`/api/flow-params${buildQuery(filters)}`)
}

export function getFlowParam(id: number) {
  return api.get<FlowParam>(`/api/flow-params/${id}`)
}

export function createFlowParam(payload: FlowParamPayload) {
  return api.post<FlowParam>('/api/flow-params', payload)
}

export function updateFlowParam(id: number, payload: Partial<FlowParamPayload>) {
  return api.put<FlowParam>(`/api/flow-params/${id}`, payload)
}

export function deleteFlowParam(id: number) {
  return api.del<void>(`/api/flow-params/${id}`)
}

export function resetFlowParam(id: number) {
  return updateFlowParam(id, {
    status: 'pending',
    step_results: {},
    current_step: 0,
    error: null,
  })
}

export function enableFlowParam(id: number) {
  return updateFlowParam(id, { enabled: true })
}

export function disableFlowParam(id: number) {
  return updateFlowParam(id, { enabled: false })
}

export function clearFlowParams(filters: FlowParamFilters = {}) {
  return api.del<{ deleted_count: number }>(`/api/flow-params/batch-clear${buildQuery(filters)}`)
}

export function batchResetFlowParams(payload: FlowParamBatchPayload) {
  return api.post<{ updated_count: number }>('/api/flow-params/batch-reset', payload)
}

export function batchEnableFlowParams(payload: FlowParamBatchPayload) {
  return api.post<{ updated_count: number }>('/api/flow-params/batch-enable', payload)
}

export function batchDisableFlowParams(payload: FlowParamBatchPayload) {
  return api.post<{ updated_count: number }>('/api/flow-params/batch-disable', payload)
}

export function importFlowParams(flowId: string, file: File) {
  const formData = new FormData()
  formData.append('flow_id', flowId)
  formData.append('file', file)
  return api.postForm<FlowParamImportResult>('/api/flow-params/import', formData)
}

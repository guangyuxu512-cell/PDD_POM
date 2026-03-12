import { api } from './index'
import type {
  PaginatedList,
  TaskParamBatchOption,
  TaskParamBatchPayload,
  TaskParam,
  TaskParamFilters,
  TaskParamImportResult,
  TaskParamPayload,
} from './types'

function buildQuery(filters: TaskParamFilters = {}) {
  const params = new URLSearchParams()

  if (filters.page) params.set('page', String(filters.page))
  if (filters.page_size) params.set('page_size', String(filters.page_size))
  if (filters.shop_id) params.set('shop_id', filters.shop_id)
  if (filters.task_name) params.set('task_name', filters.task_name)
  if (filters.status) params.set('status', filters.status)
  if (filters.batch_id) params.set('batch_id', filters.batch_id)
  if (filters.updated_from) params.set('updated_from', filters.updated_from)
  if (filters.updated_to) params.set('updated_to', filters.updated_to)
  if (filters.sort_by) params.set('sort_by', filters.sort_by)
  if (filters.sort_order) params.set('sort_order', filters.sort_order)

  const query = params.toString()
  return query ? `?${query}` : ''
}

export function listTaskParams(filters: TaskParamFilters = {}) {
  return api.get<PaginatedList<TaskParam>>(`/api/task-params${buildQuery(filters)}`)
}

export function listTaskParamBatchOptions(filters: TaskParamFilters = {}) {
  return api.get<TaskParamBatchOption[]>(`/api/task-params/batch-options${buildQuery(filters)}`)
}

export function createTaskParam(payload: TaskParamPayload) {
  return api.post<TaskParam>('/api/task-params', payload)
}

export function updateTaskParam(id: number, payload: Partial<TaskParamPayload>) {
  return api.put<TaskParam>(`/api/task-params/${id}`, payload)
}

export function enableTaskParam(id: number) {
  return api.put<TaskParam>(`/api/task-params/${id}/enable`)
}

export function disableTaskParam(id: number) {
  return api.put<TaskParam>(`/api/task-params/${id}/disable`)
}

export function resetTaskParam(id: number) {
  return api.put<TaskParam>(`/api/task-params/${id}/reset`)
}

export function deleteTaskParam(id: number) {
  return api.del<void>(`/api/task-params/${id}`)
}

export function clearTaskParams(filters: TaskParamFilters = {}) {
  return api.del<{ deleted_count: number }>(`/api/task-params/clear${buildQuery(filters)}`)
}

export function batchResetTaskParams(payload: TaskParamBatchPayload) {
  return api.put<{ updated_count: number }>('/api/task-params/batch-reset', payload)
}

export function batchEnableTaskParams(payload: TaskParamBatchPayload) {
  return api.put<{ updated_count: number }>('/api/task-params/batch-enable', payload)
}

export function batchDisableTaskParams(payload: TaskParamBatchPayload) {
  return api.put<{ updated_count: number }>('/api/task-params/batch-disable', payload)
}

export function importTaskParamsCsv(taskName: string, file: File) {
  const formData = new FormData()
  formData.append('task_name', taskName)
  formData.append('file', file)
  return api.postForm<TaskParamImportResult>('/api/task-params/import-csv', formData)
}

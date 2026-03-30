import { api } from './index'
import type { BatchRequest, BatchResponse } from './types'

export function createBatch(payload: BatchRequest) {
  return api.post<BatchResponse>('/api/execute/batch', payload)
}

export function stopBatch(batchId?: string) {
  return api.post<BatchResponse>(
    '/api/execute/stop',
    batchId ? { batch_id: batchId } : undefined
  )
}

export function createBatchStatusEventSource(batchId?: string) {
  const query = batchId ? `?batch_id=${encodeURIComponent(batchId)}` : ''
  return new EventSource(`/api/execute/status${query}`)
}

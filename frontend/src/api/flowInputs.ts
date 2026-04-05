import { api } from './index'
import type { FlowInputSet, PaginatedList } from './types'

export function listFlowInputSets(flowId: string) {
  return api.get<PaginatedList<FlowInputSet>>(`/api/flows/${flowId}/input-sets`)
}

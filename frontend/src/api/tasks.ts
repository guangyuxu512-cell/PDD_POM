import { api } from './index'
import type { AvailableTask } from './types'

interface AvailableTasksResponse {
  tasks: AvailableTask[]
}

export async function listAvailableTasks() {
  const response = await api.get<AvailableTasksResponse>('/api/tasks/available')
  return response.tasks
}

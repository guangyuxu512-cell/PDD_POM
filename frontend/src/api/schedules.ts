import { api } from './index'
import type { PaginatedList, Schedule, SchedulePayload } from './types'

export function listSchedules() {
  return api.get<PaginatedList<Schedule>>('/api/schedules')
}

export function createSchedule(payload: SchedulePayload) {
  return api.post<Schedule>('/api/schedules', payload)
}

export function updateSchedule(scheduleId: string, payload: Partial<SchedulePayload>) {
  return api.put<Schedule>(`/api/schedules/${scheduleId}`, payload)
}

export function deleteSchedule(scheduleId: string) {
  return api.del<void>(`/api/schedules/${scheduleId}`)
}

export function pauseSchedule(scheduleId: string) {
  return api.post<Schedule>(`/api/schedules/${scheduleId}/pause`)
}

export function resumeSchedule(scheduleId: string) {
  return api.post<Schedule>(`/api/schedules/${scheduleId}/resume`)
}

import { api } from './index'
import type { SettingItem } from './types'

export function listSettings() {
  return api.get<{ list: SettingItem[] }>('/api/settings')
}

export function updateSetting(key: string, value: string | null) {
  return api.put(`/api/settings/${key}`, { value })
}

export function batchUpdateSettings(items: Array<{ key: string; value: string | null }>) {
  return api.post('/api/settings/batch', { items })
}

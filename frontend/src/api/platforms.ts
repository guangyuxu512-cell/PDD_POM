import { api } from './index'
import type { Platform } from './types'

export function listPlatforms() {
  return api.get<{ list: Platform[] }>('/api/platforms')
}

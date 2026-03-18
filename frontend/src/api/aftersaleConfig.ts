import { api } from './index'

export function getAftersaleConfig(shopId: string) {
  return api.get<Record<string, any>>(`/api/aftersale-config/${shopId}`)
}

export function updateAftersaleConfig(shopId: string, data: Record<string, any>) {
  return api.put<Record<string, any>>(`/api/aftersale-config/${shopId}`, data)
}

export function getAllAftersaleConfigs() {
  return api.get<Array<Record<string, any>>>('/api/aftersale-config')
}

export function deleteAftersaleConfig(shopId: string) {
  return api.del<void>(`/api/aftersale-config/${shopId}`)
}

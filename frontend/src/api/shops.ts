import { api } from './index'
import type { PaginatedList, Shop, ShopPayload } from './types'

export function listShops() {
  return api.get<PaginatedList<Shop>>('/api/shops')
}

export function createShop(payload: ShopPayload) {
  return api.post<Shop>('/api/shops', payload)
}

export function updateShop(shopId: string, payload: Partial<ShopPayload>) {
  return api.put<Shop>(`/api/shops/${shopId}`, payload)
}

export function deleteShop(shopId: string) {
  return api.del<void>(`/api/shops/${shopId}`)
}

export function openShopBrowser(shopId: string) {
  return api.post(`/api/shops/${shopId}/open`)
}

export function checkShopStatus(shopId: string) {
  return api.post<{ status: string }>(`/api/shops/${shopId}/check-status`)
}

export function testShopEmailConnection(shopId: string) {
  return api.post(`/api/shops/${shopId}/test-email`)
}

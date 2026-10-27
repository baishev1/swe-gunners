import { apiClient } from './client'
import type { Order, OrderCreatePayload } from '@/shared/types'

export async function createOrder(data: OrderCreatePayload): Promise<Order> {
  const response = await apiClient.post<Order>('/orders', data)
  return response.data
}

export async function getOrderDetail(orderId: string): Promise<Order> {
  const response = await apiClient.get<Order>('/orders/detail', {
    params: { order_id: orderId },
  })
  return response.data
}

export async function listOrders(params?: {
  user_id?: string
  event_id?: string
}): Promise<Order[]> {
  const response = await apiClient.get<Order[]>('/orders', { params })
  return response.data
}

export async function cancelOrder(orderId: string): Promise<Order> {
  const response = await apiClient.post<Order>('/orders/cancel', null, {
    params: { order_id: orderId },
  })
  return response.data
}

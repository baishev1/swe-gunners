import { apiClient } from './client'
import type { Payment, PaymentSimulatePayload } from '@/shared/types'

export async function simulatePayment(data: PaymentSimulatePayload): Promise<Payment> {
  const response = await apiClient.post<Payment>('/payments/simulate', data)
  return response.data
}

export async function getPaymentDetail(orderId: string): Promise<Payment> {
  const response = await apiClient.get<Payment>('/payments/detail', {
    params: { order_id: orderId },
  })
  return response.data
}

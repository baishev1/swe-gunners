import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createOrder, simulatePayment } from '@/shared/api'
import { Button, Card, CardContent, CardFooter, CardHeader, CardTitle, Input } from '@/shared/ui'
import type { OrderItemCreate } from '@/shared/types'

export interface CheckoutTicketTypeOption {
  id: string
  name: string
  price_kzt: number
}

interface CheckoutFormProps {
  eventId: string
  ticketTypes: CheckoutTicketTypeOption[]
}

export function CheckoutForm({ eventId, ticketTypes }: CheckoutFormProps) {
  const navigate = useNavigate()
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [quantities, setQuantities] = useState<Record<string, number>>(
    Object.fromEntries(ticketTypes.map((t, idx) => [t.id, idx === 0 ? 1 : 0])),
  )
  const [simulateFailure, setSimulateFailure] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleQuantityChange = (id: string, delta: number) => {
    setQuantities((prev) => {
      const current = prev[id] || 0
      const next = Math.max(0, current + delta)
      return { ...prev, [id]: next }
    })
  }

  const selectedItems: OrderItemCreate[] = ticketTypes
    .filter((t) => (quantities[t.id] || 0) > 0)
    .map((t) => ({
      ticket_type_id: t.id,
      ticket_type_name: t.name,
      unit_price_kzt: t.price_kzt,
      quantity: quantities[t.id],
    }))

  const totalAmountKzt = selectedItems.reduce(
    (sum, item) => sum + item.unit_price_kzt * item.quantity,
    0,
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!customerName.trim() || !customerEmail.trim()) {
      setErrorMessage('Please fill in your name and email address.')
      return
    }

    if (selectedItems.length === 0) {
      setErrorMessage('Please select at least one ticket.')
      return
    }

    setIsLoading(true)
    try {
      const order = await createOrder({
        event_id: eventId,
        customer_name: customerName,
        customer_email: customerEmail,
        items: selectedItems,
      })

      if (totalAmountKzt === 0) {
        navigate(`/tickets?order_id=${order.id}`)
        return
      }

      const payment = await simulatePayment({
        order_id: order.id,
        simulate_failure: simulateFailure,
      })

      if (payment.status === 'succeeded') {
        navigate(`/tickets?order_id=${order.id}`)
      } else {
        setErrorMessage('Payment simulation failed. Order remains pending.')
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An error occurred during checkout.'
      setErrorMessage(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Select Tickets</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {ticketTypes.map((type) => (
            <div
              key={type.id}
              className="flex items-center justify-between border-b pb-3 last:border-0"
            >
              <div>
                <p className="font-medium text-sm text-foreground">{type.name}</p>
                <p className="text-muted-foreground text-xs">{type.price_kzt} ₸</p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="icon-xs"
                  onClick={() => handleQuantityChange(type.id, -1)}
                  disabled={isLoading || (quantities[type.id] || 0) === 0}
                >
                  -
                </Button>
                <span className="w-6 text-center text-sm font-semibold">
                  {quantities[type.id] || 0}
                </span>
                <Button
                  type="button"
                  variant="outline"
                  size="icon-xs"
                  onClick={() => handleQuantityChange(type.id, 1)}
                  disabled={isLoading}
                >
                  +
                </Button>
              </div>
            </div>
          ))}

          <div className="flex justify-between pt-2 border-t font-semibold text-base">
            <span>Total:</span>
            <span>{totalAmountKzt} ₸</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Attendee Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Full Name</label>
            <Input
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="e.g. Arman Bekov"
              required
              disabled={isLoading}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">Email Address</label>
            <Input
              type="email"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              placeholder="e.g. arman@example.kz"
              required
              disabled={isLoading}
            />
          </div>

          {totalAmountKzt > 0 && (
            <div className="rounded-md border p-3 bg-muted/20 text-xs text-muted-foreground space-y-2">
              <p className="font-semibold text-foreground">Demonstration Payment Simulation</p>
              <p>
                No real payments are collected. Clicking the button below processes a simulated KZT
                payment and issues verified QR tickets.
              </p>
              <label className="flex items-center gap-2 pt-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={simulateFailure}
                  onChange={(e) => setSimulateFailure(e.target.checked)}
                  className="rounded border-input text-primary focus:ring-primary"
                />
                <span>Simulate payment failure</span>
              </label>
            </div>
          )}

          {errorMessage && (
            <div className="rounded-md bg-destructive/10 p-3 text-xs text-destructive">
              {errorMessage}
            </div>
          )}
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading
              ? 'Processing...'
              : totalAmountKzt === 0
                ? 'Complete Free Registration'
                : `Pay ${totalAmountKzt} ₸ (Simulate)`}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}

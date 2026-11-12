import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listOrders } from '@/shared/api'
import { Button } from '@/shared/ui'
import { OrderCard } from '@/entities/order'

export function OrdersPage() {
  const {
    data: orders = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['orders'],
    queryFn: () => listOrders(),
  })

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">My Orders</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Review past purchases and registrations.
          </p>
        </div>
        <Button asChild size="sm">
          <Link to="/checkout">New Order</Link>
        </Button>
      </div>

      {isLoading && (
        <div className="text-center py-12 text-sm text-muted-foreground">
          Loading your orders...
        </div>
      )}

      {error && (
        <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load orders.
        </div>
      )}

      {!isLoading && !error && orders.length === 0 && (
        <div className="text-center py-12 rounded-xl border border-dashed border-border p-8">
          <p className="text-muted-foreground text-sm">No orders found yet.</p>
          <Button asChild className="mt-4" size="sm">
            <Link to="/checkout">Browse Tickets</Link>
          </Button>
        </div>
      )}

      <div className="space-y-4">
        {orders.map((order) => (
          <OrderCard key={order.id} order={order} />
        ))}
      </div>
    </div>
  )
}

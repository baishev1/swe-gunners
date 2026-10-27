import { useTicketTypes } from '@/entities/ticket-type'
import { getErrorMessage } from '@/shared/api'
import { formatPrice } from '@/shared/lib/format'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardAction, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { FieldError } from '@/shared/ui/field'

import { useUpdateTicketType } from '../model/use-ticket-type-mutations'
import { TicketTypeForm } from './ticket-type-form'

export function TicketTypeManager({ eventId }: { eventId: string }) {
  const ticketTypes = useTicketTypes(eventId, true)
  const updateTicketType = useUpdateTicketType()

  return (
    <div className="flex flex-col gap-6">
      {ticketTypes.data?.map((ticketType) => (
        <Card key={ticketType.id}>
          <CardHeader>
            <CardTitle>
              {ticketType.name} · {formatPrice(ticketType.price)}
            </CardTitle>
            <CardDescription>
              {ticketType.available} available · {ticketType.reserved_count} reserved ·{' '}
              {ticketType.sold_count} sold of {ticketType.quantity}
            </CardDescription>
            <CardAction className="flex items-center gap-2">
              {ticketType.is_hidden && <Badge variant="outline">Hidden</Badge>}
              <Button
                variant="outline"
                size="sm"
                disabled={updateTicketType.isPending}
                onClick={() =>
                  updateTicketType.mutate({ id: ticketType.id, is_hidden: !ticketType.is_hidden })
                }
              >
                {ticketType.is_hidden ? 'Show' : 'Hide'}
              </Button>
            </CardAction>
          </CardHeader>
        </Card>
      ))}
      {updateTicketType.isError && (
        <FieldError>{getErrorMessage(updateTicketType.error)}</FieldError>
      )}
      <TicketTypeForm eventId={eventId} />
    </div>
  )
}

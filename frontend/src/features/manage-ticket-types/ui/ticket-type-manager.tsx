import { useTranslation } from 'react-i18next'

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
  const { t } = useTranslation()
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
              {t('ticketTypes.stats', {
                available: ticketType.available,
                reserved: ticketType.reserved_count,
                sold: ticketType.sold_count,
                quantity: ticketType.quantity,
              })}
            </CardDescription>
            <CardAction className="flex items-center gap-2">
              {ticketType.is_hidden && <Badge variant="outline">{t('ticketTypes.hidden')}</Badge>}
              <Button
                variant="outline"
                size="sm"
                disabled={updateTicketType.isPending}
                onClick={() =>
                  updateTicketType.mutate({ id: ticketType.id, is_hidden: !ticketType.is_hidden })
                }
              >
                {ticketType.is_hidden ? t('ticketTypes.show') : t('ticketTypes.hide')}
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

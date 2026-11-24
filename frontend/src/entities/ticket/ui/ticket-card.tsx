import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { downloadTicketPdf, getTicketQrSvg } from '@/shared/api'
import { Badge, Button, Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/shared/ui'
import { Skeleton } from '@/shared/ui/skeleton'
import type { Ticket } from '@/shared/types'
import { ticketSeatLabel } from '@/entities/seating'

interface TicketCardProps {
  ticket: Ticket
}

export function TicketCard({ ticket }: TicketCardProps) {
  const { t } = useTranslation()
  const isCheckedIn = ticket.status === 'checked_in'
  const isValid = ticket.status === 'valid'
  // Cancelled and refunded tickets no longer admit anyone, so they show no QR (SRS 4.9).
  const isAdmissible = isValid || isCheckedIn
  const qr = useQuery({
    queryKey: ['ticket-qr', ticket.id],
    queryFn: () => getTicketQrSvg(ticket.id),
    enabled: isAdmissible,
    staleTime: Infinity,
  })

  const handleDownload = async () => {
    const url = URL.createObjectURL(await downloadTicketPdf(ticket.id))
    const link = document.createElement('a')
    link.href = url
    link.download = `ticket-${ticket.id}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Card className="overflow-hidden border-border/80">
      <CardHeader className="bg-muted/30 pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold">{ticket.ticket_type_name}</CardTitle>
          <Badge variant={isValid ? 'success' : isCheckedIn ? 'secondary' : 'destructive'}>
            {t(`eventAttendees.statuses.${ticket.status}`, { defaultValue: ticket.status })}
          </Badge>
        </div>
        {ticket.section && ticket.row && ticket.seat && (
          <p className="text-sm font-semibold">
            {ticketSeatLabel(t, ticket.section, ticket.row, ticket.seat)}
          </p>
        )}
        <p className="text-muted-foreground text-xs">{t('tickets.id', { id: ticket.id })}</p>
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-muted-foreground block">{t('tickets.attendee')}</span>
            <span className="font-medium text-foreground">{ticket.attendee_name}</span>
          </div>
          <div>
            <span className="text-muted-foreground block">{t('tickets.email')}</span>
            <span className="font-medium text-foreground truncate block">
              {ticket.attendee_email}
            </span>
          </div>
        </div>

        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 p-4 text-center">
          {!isAdmissible ? (
            <p className="text-muted-foreground text-sm">{t('tickets.notAdmissible')}</p>
          ) : qr.data ? (
            <>
              {/* White padding keeps the quiet zone when the page is in dark mode. */}
              <img
                src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(qr.data)}`}
                alt={t('tickets.qrAlt', { id: ticket.id })}
                className="size-56 rounded-md bg-white p-2"
              />
              <p className="text-muted-foreground mt-2 text-xs">{t('tickets.showQr')}</p>
            </>
          ) : qr.isError ? (
            <p className="text-destructive text-sm">{t('tickets.qrFailed')}</p>
          ) : (
            <Skeleton className="size-56" />
          )}
        </div>
      </CardContent>
      <CardFooter className="border-t bg-muted/10 pt-3">
        <Button variant="outline" size="sm" className="w-full" onClick={handleDownload}>
          <Download className="size-3.5 mr-1.5" />
          {t('tickets.downloadPdf')}
        </Button>
      </CardFooter>
    </Card>
  )
}

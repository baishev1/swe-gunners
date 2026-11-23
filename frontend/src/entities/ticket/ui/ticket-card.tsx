import { Download, QrCode } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { downloadTicketPdf } from '@/shared/api'
import { Badge, Button, Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/shared/ui'
import type { Ticket } from '@/shared/types'

interface TicketCardProps {
  ticket: Ticket
}

export function TicketCard({ ticket }: TicketCardProps) {
  const { t } = useTranslation()
  const isCheckedIn = ticket.status === 'checked_in'
  const isValid = ticket.status === 'valid'

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
          <QrCode className="size-24 text-foreground/80 mb-2 stroke-[1.5]" />
          <p className="text-[11px] font-mono text-muted-foreground break-all px-2">
            {ticket.qr_token.slice(0, 24)}...
          </p>
          <p className="text-[10px] text-muted-foreground mt-1">{t('tickets.showQr')}</p>
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

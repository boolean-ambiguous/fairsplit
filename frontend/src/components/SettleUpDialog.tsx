import { useState } from 'react'
import { Button, Dialog, DialogActions, DialogContent, Stack, Typography } from '@mui/material'
import { api, ApiError } from '../api/client'
import type { GroupDetail } from '../api/types'
import { formatCurrency } from '../money'
import { memberDisplayName } from '../splitSummary'

interface Props {
  open: boolean
  group: GroupDetail
  myMemberId: string | null
  onClose: () => void
  onSettled: () => void
}

export default function SettleUpDialog({ open, group, myMemberId, onClose, onSettled }: Props) {
  const [error, setError] = useState<string | null>(null)
  const membersById = Object.fromEntries(group.members.map((m) => [m.id, m]))

  const markPaid = async (otherId: string, cents: number) => {
    if (!myMemberId) return
    setError(null)
    try {
      const [from, to] = cents > 0 ? [otherId, myMemberId] : [myMemberId, otherId]
      await api.recordSettlement(group.id, {
        from_member: from,
        to_member: to,
        amount: (Math.abs(cents) / 100).toFixed(2),
      })
      onSettled()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogContent>
        <Typography variant="h6" sx={{ fontWeight: 500, mb: 2 }}>
          Settle up in {group.name}
        </Typography>
        {group.my_positions.length === 0 ? (
          <Typography color="text.secondary">Nothing to settle. You're all square. 🎉</Typography>
        ) : (
          <Stack spacing={1}>
            {group.my_positions.map((p) => {
              const otherName = memberDisplayName(p.member_id, myMemberId, membersById)
              const line =
                p.balance_cents > 0
                  ? `${otherName} owes you ${formatCurrency(p.balance_cents, group.currency)}`
                  : `You owe ${otherName} ${formatCurrency(-p.balance_cents, group.currency)}`
              return (
                <Stack
                  key={p.member_id}
                  direction="row"
                  spacing={1.5}
                  sx={{ p: 1.25, borderRadius: '8px', bgcolor: 'background.default', alignItems: 'center', justifyContent: 'space-between' }}
                >
                  <Typography variant="body2">{line}</Typography>
                  <Button size="small" variant="outlined" sx={{ flex: 'none' }} onClick={() => markPaid(p.member_id, p.balance_cents)}>
                    Mark as paid
                  </Button>
                </Stack>
              )
            })}
          </Stack>
        )}
        {error && (
          <Typography color="error" variant="body2" sx={{ mt: 1.5 }}>
            {error}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Done</Button>
      </DialogActions>
    </Dialog>
  )
}

import { Box, Button, Dialog, DialogActions, DialogContent, Stack, Typography } from '@mui/material'
import type { Expense, GroupDetail } from '../api/types'
import { formatCurrency } from '../money'
import { memberDisplayName, splitSummary } from '../splitSummary'

interface Props {
  open: boolean
  group: GroupDetail
  expense: Expense | null
  myMemberId: string | null
  onClose: () => void
  onEdit: (expense: Expense) => void
  onDelete: (expense: Expense) => void
}

function formatDate(iso: string) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function formatDateTime(iso: string) {
  const d = new Date(iso)
  return (
    d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
    ' at ' +
    d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
  )
}

export default function ExpenseDetailDialog({ open, group, expense, myMemberId, onClose, onEdit, onDelete }: Props) {
  if (!expense) return null
  const membersById = Object.fromEntries(group.members.map((m) => [m.id, m]))
  const paidByText = memberDisplayName(expense.payer_id, myMemberId, membersById)
  const createdByText = memberDisplayName(expense.created_by, myMemberId, membersById)
  const history = [...expense.history].reverse()

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogContent>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1.5} sx={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                {expense.description}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
                Paid by {paidByText} · {formatDate(expense.date)}
              </Typography>
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 500, flex: 'none' }}>
              {formatCurrency(expense.amount_cents, group.currency)}
            </Typography>
          </Stack>
          <Typography variant="body2" color="success.main">
            {splitSummary(expense, myMemberId, membersById, group.currency)}
          </Typography>
          {expense.notes && (
            <Typography variant="body2" sx={{ bgcolor: 'background.default', borderRadius: '8px', p: 1.25 }}>
              {expense.notes}
            </Typography>
          )}
          <Stack direction="row" spacing={1.5}>
            <Button variant="outlined" size="small" sx={{ flex: 1 }} onClick={() => onEdit(expense)}>
              Edit expense
            </Button>
            {expense.can_delete && (
              <Button variant="outlined" color="error" size="small" sx={{ flex: 1 }} onClick={() => onDelete(expense)}>
                Delete expense
              </Button>
            )}
          </Stack>
          <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 1.75 }}>
            <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              Version history
            </Typography>
            <Box sx={{ borderBottom: 1, borderColor: 'divider', py: 1.25 }}>
              <Typography variant="body2">Created by {createdByText}</Typography>
              <Typography variant="caption" color="text.secondary">
                {formatDateTime(expense.created_at)}
              </Typography>
            </Box>
            {history.map((h, i) => (
              <Box key={i} sx={{ borderBottom: 1, borderColor: 'divider', py: 1.25 }}>
                <Typography variant="body2">
                  Edited by {memberDisplayName(h.changed_by, myMemberId, membersById)}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  {formatDateTime(h.changed_at)}
                </Typography>
                {h.changes.map((c, j) => (
                  <Typography key={j} variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                    {c.field}: {c.previous} → {c.updated}
                  </Typography>
                ))}
              </Box>
            ))}
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}

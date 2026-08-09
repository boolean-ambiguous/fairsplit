import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Box, Button, Container, IconButton, Stack, Typography } from '@mui/material'
import { api } from '../api/client'
import type { Expense, GroupDetail as GroupDetailData } from '../api/types'
import { colorFor, formatCurrency, initials } from '../money'
import { memberDisplayName, splitSummary } from '../splitSummary'
import { useAuth } from '../auth/AuthContext'
import AppHeader from '../components/AppHeader'
import AddExpenseDialog from '../components/AddExpenseDialog'
import ExpenseDetailDialog from '../components/ExpenseDetailDialog'
import GroupEditDialog from '../components/GroupEditDialog'
import SettleUpDialog from '../components/SettleUpDialog'
import { EditIcon, TrashIcon } from '../components/icons'

function formatDate(iso: string) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function GroupDetail() {
  const { groupId } = useParams<{ groupId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [group, setGroup] = useState<GroupDetailData | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [forbidden, setForbidden] = useState(false)

  const [showAddExpense, setShowAddExpense] = useState(false)
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null)
  const [viewingExpense, setViewingExpense] = useState<Expense | null>(null)
  const [showEditGroup, setShowEditGroup] = useState(false)
  const [showSettleUp, setShowSettleUp] = useState(false)

  const refresh = () => {
    if (!groupId) return
    api
      .getGroup(groupId)
      .then(setGroup)
      .catch((err) => {
        if (err.status === 404) setNotFound(true)
        if (err.status === 403) setForbidden(true)
      })
  }

  useEffect(refresh, [groupId])

  if (notFound || forbidden) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Alert severity="error">
          {notFound ? 'Group not found.' : "You're not a member of this group."}
        </Alert>
      </Container>
    )
  }
  if (!group) return null

  const membersById = Object.fromEntries(group.members.map((m) => [m.id, m]))
  const myMember = group.members.find((m) => m.user_id === user?.id) ?? null
  const myMemberId = myMember?.id ?? null

  const sortedExpenses = [...group.expenses].sort((a, b) => b.date.localeCompare(a.date))
  const sortedSettlements = [...group.settlement_history].sort((a, b) =>
    b.settled_at.localeCompare(a.settled_at),
  )

  return (
    <>
      <AppHeader title={group.name} onBack={() => navigate('/')} onEditGroup={() => setShowEditGroup(true)} />
      <Box sx={{ px: 2.5, pb: 12, display: 'flex', flexDirection: 'column', gap: 2.75 }}>
        <Stack direction="row" spacing={0.75} sx={{ flexWrap: 'wrap', rowGap: 0.75 }}>
          {group.members.map((m) => (
            <Stack
              key={m.id}
              direction="row"
              spacing={0.75}
              sx={{ bgcolor: 'background.paper', borderRadius: '20px', pl: 0.5, pr: 1.25, py: 0.5, alignItems: 'center' }}
            >
              <Box
                sx={{
                  width: 20,
                  height: 20,
                  borderRadius: '50%',
                  bgcolor: colorFor(m.id),
                  color: '#e7e5fe',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 9,
                }}
              >
                {initials(m.id === myMemberId ? user?.name ?? '' : m.name)}
              </Box>
              <Typography variant="caption">{m.id === myMemberId ? 'You' : m.name}</Typography>
            </Stack>
          ))}
        </Stack>

        <Box>
          {group.my_positions.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              You're all settled up in this group! 🎉
            </Typography>
          ) : (
            <Stack spacing={1}>
              {group.my_positions.map((p) => (
                <Box key={p.member_id} sx={{ bgcolor: 'background.paper', borderRadius: '8px', p: 1.25 }}>
                  <Typography variant="body2">
                    {p.balance_cents > 0
                      ? `${memberDisplayName(p.member_id, myMemberId, membersById)} owes you ${formatCurrency(p.balance_cents, group.currency)}`
                      : `You owe ${memberDisplayName(p.member_id, myMemberId, membersById)} ${formatCurrency(-p.balance_cents, group.currency)}`}
                  </Typography>
                </Box>
              ))}
            </Stack>
          )}
        </Box>

        <Stack direction="row" spacing={1.25}>
          <Button variant="outlined" fullWidth onClick={() => { setEditingExpense(null); setShowAddExpense(true) }}>
            Add expense
          </Button>
          <Button variant="outlined" color="inherit" fullWidth onClick={() => setShowSettleUp(true)}>
            Settle up
          </Button>
        </Stack>

        <Box>
          <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            Expenses
          </Typography>
          <Stack>
            {sortedExpenses.map((e) => (
              <Box
                key={e.id}
                onClick={() => setViewingExpense(e)}
                sx={{ py: 1.5, borderBottom: 1, borderColor: 'divider', cursor: 'pointer' }}
              >
                <Stack direction="row" spacing={1.25} sx={{ justifyContent: 'space-between' }}>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {e.description}
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ flex: 'none', alignItems: 'center' }}>
                    <Typography variant="body2" sx={{ fontWeight: 500, minWidth: 64, textAlign: 'right' }}>
                      {formatCurrency(e.amount_cents, group.currency)}
                    </Typography>
                    <Stack direction="row" spacing={0.75} sx={{ width: 60, justifyContent: 'flex-end' }}>
                      <IconButton
                        size="small"
                        title="Edit expense"
                        onClick={(evt) => {
                          evt.stopPropagation()
                          setEditingExpense(e)
                          setShowAddExpense(true)
                        }}
                        sx={{ width: 26, height: 26, border: 1, borderColor: 'primary.main', color: 'primary.main', borderRadius: '6px' }}
                      >
                        <EditIcon size={13} />
                      </IconButton>
                      {e.can_delete && (
                        <IconButton
                          size="small"
                          title="Delete expense"
                          onClick={async (evt) => {
                            evt.stopPropagation()
                            if (!groupId) return
                            if (!window.confirm('Delete this expense?')) return
                            await api.deleteExpense(groupId, e.id)
                            refresh()
                          }}
                          sx={{ width: 26, height: 26, border: 1, borderColor: 'error.main', color: 'error.main', borderRadius: '6px' }}
                        >
                          <TrashIcon size={13} />
                        </IconButton>
                      )}
                    </Stack>
                  </Stack>
                </Stack>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
                  Paid by {memberDisplayName(e.payer_id, myMemberId, membersById)} · {formatDate(e.date)}
                </Typography>
                <Typography variant="caption" color="success.main" sx={{ display: 'block' }}>
                  {splitSummary(e, myMemberId, membersById, group.currency)}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Box>

        {sortedSettlements.length > 0 && (
          <Box>
            <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              Settled up
            </Typography>
            <Stack>
              {sortedSettlements.map((s) => (
                <Box key={s.id} sx={{ py: 1.5, borderBottom: 1, borderColor: 'divider' }}>
                  <Stack direction="row" spacing={1.25} sx={{ justifyContent: 'space-between' }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {memberDisplayName(s.from_member, myMemberId, membersById)} paid{' '}
                      {memberDisplayName(s.to_member, myMemberId, membersById)}
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500, flex: 'none' }}>
                      {formatCurrency(s.amount_cents, group.currency)}
                    </Typography>
                  </Stack>
                  <Typography variant="caption" color="text.secondary">
                    Settled {formatDate(s.settled_at.slice(0, 10))}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        )}
      </Box>

      <AddExpenseDialog
        open={showAddExpense}
        group={group}
        myMemberId={myMemberId}
        editing={editingExpense}
        onClose={() => setShowAddExpense(false)}
        onSaved={() => {
          setShowAddExpense(false)
          setViewingExpense(null)
          refresh()
        }}
      />
      <ExpenseDetailDialog
        open={!!viewingExpense}
        group={group}
        expense={viewingExpense ? group.expenses.find((e) => e.id === viewingExpense.id) ?? viewingExpense : null}
        myMemberId={myMemberId}
        onClose={() => setViewingExpense(null)}
        onEdit={(e) => {
          setEditingExpense(e)
          setViewingExpense(null)
          setShowAddExpense(true)
        }}
        onDelete={async (e) => {
          if (!groupId) return
          if (!window.confirm('Delete this expense?')) return
          await api.deleteExpense(groupId, e.id)
          setViewingExpense(null)
          refresh()
        }}
      />
      <GroupEditDialog
        open={showEditGroup}
        group={group}
        onClose={() => setShowEditGroup(false)}
        onSaved={() => {
          setShowEditGroup(false)
          refresh()
        }}
        onDeleted={() => {
          setShowEditGroup(false)
          navigate('/', { replace: true })
        }}
      />
      <SettleUpDialog
        open={showSettleUp}
        group={group}
        myMemberId={myMemberId}
        onClose={() => setShowSettleUp(false)}
        onSettled={() => {
          refresh()
        }}
      />
    </>
  )
}

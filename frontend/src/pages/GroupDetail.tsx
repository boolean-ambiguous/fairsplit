import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  Container,
  FormControlLabel,
  List,
  ListItem,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { api, ApiError } from '../api/client'
import type { GroupDetail as GroupDetailData, SplitMode } from '../api/types'
import { formatCents } from '../money'

export default function GroupDetail() {
  const { groupId } = useParams<{ groupId: string }>()
  const [group, setGroup] = useState<GroupDetailData | null>(null)
  const [notFound, setNotFound] = useState(false)

  const [memberName, setMemberName] = useState('')
  const [memberError, setMemberError] = useState<string | null>(null)

  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [payerId, setPayerId] = useState('')
  const [participantIds, setParticipantIds] = useState<Set<string>>(new Set())
  const [splitMode, setSplitMode] = useState<SplitMode>('even')
  const [shares, setShares] = useState<Record<string, string>>({})
  const [expenseError, setExpenseError] = useState<string | null>(null)

  const refresh = () => {
    if (!groupId) return
    api
      .getGroup(groupId)
      .then((data) => {
        setGroup(data)
        setParticipantIds(new Set(data.members.map((m) => m.id)))
        setPayerId((prev) => prev || data.members[0]?.id || '')
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setNotFound(true)
      })
  }

  useEffect(refresh, [groupId])

  if (notFound) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Alert severity="error">Group not found.</Alert>
      </Container>
    )
  }
  if (!group) return null

  const handleAddMember = async (event: React.FormEvent) => {
    event.preventDefault()
    setMemberError(null)
    try {
      await api.addMember(group.id, memberName)
      setMemberName('')
      refresh()
    } catch (err) {
      if (err instanceof ApiError) setMemberError(err.message)
    }
  }

  const toggleParticipant = (id: string) => {
    setParticipantIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleAddExpense = async (event: React.FormEvent) => {
    event.preventDefault()
    setExpenseError(null)
    try {
      await api.addExpense(group.id, {
        description,
        amount,
        payer_id: payerId,
        participant_ids: Array.from(participantIds),
        split_mode: splitMode,
        exact_shares:
          splitMode === 'exact'
            ? Object.fromEntries(
                Array.from(participantIds).map((id) => [id, shares[id] ?? '0']),
              )
            : undefined,
      })
      setDescription('')
      setAmount('')
      setShares({})
      refresh()
    } catch (err) {
      if (err instanceof ApiError) setExpenseError(err.message)
    }
  }

  const memberName_ = (id: string) => group.members.find((m) => m.id === id)?.name ?? id

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        {group.name}
      </Typography>

      <Typography variant="h6" component="h2" sx={{ mt: 3 }}>
        Members
      </Typography>
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Box component="form" onSubmit={handleAddMember}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-end' }}>
              <TextField
                label="Add member"
                value={memberName}
                onChange={(e) => setMemberName(e.target.value)}
                size="small"
              />
              <Button type="submit" variant="contained">
                Add
              </Button>
            </Stack>
          </Box>
          {memberError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {memberError}
            </Alert>
          )}
          <List dense>
            {group.members.map((m) => (
              <ListItem key={m.id} disableGutters>
                {m.name}
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      <Typography variant="h6" component="h2">
        Balances
      </Typography>
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <List dense>
            {group.balances.map((b) => (
              <ListItem key={b.member_id} disableGutters>
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                  <Typography>{memberName_(b.member_id)}:</Typography>
                  {b.balance_cents > 0 && (
                    <Chip
                      size="small"
                      color="success"
                      label={`is owed ${formatCents(b.balance_cents)}`}
                    />
                  )}
                  {b.balance_cents < 0 && (
                    <Chip
                      size="small"
                      color="error"
                      label={`owes ${formatCents(-b.balance_cents)}`}
                    />
                  )}
                  {b.balance_cents === 0 && (
                    <Chip size="small" label="settled up" variant="outlined" />
                  )}
                </Stack>
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      <Typography variant="h6" component="h2">
        Settle up
      </Typography>
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          {group.settlements.length === 0 ? (
            <Typography color="text.secondary">
              No payments needed — everyone is settled up.
            </Typography>
          ) : (
            <List dense>
              {group.settlements.map((s, i) => (
                <ListItem key={i} disableGutters>
                  <strong>{memberName_(s.from_member)}</strong>&nbsp;pays&nbsp;
                  <strong>{memberName_(s.to_member)}</strong>&nbsp;
                  {formatCents(s.amount_cents)}
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      <Typography variant="h6" component="h2">
        Expenses
      </Typography>
      <Card variant="outlined">
        <CardContent>
          {group.members.length === 0 ? (
            <Typography color="text.secondary">
              Add members before recording expenses.
            </Typography>
          ) : (
            <Box component="form" onSubmit={handleAddExpense}>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
                  <TextField
                    label="Description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    size="small"
                    required
                  />
                  <TextField
                    label="Amount"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    size="small"
                    placeholder="0.00"
                    required
                  />
                  <TextField
                    select
                    label="Paid by"
                    value={payerId}
                    onChange={(e) => setPayerId(e.target.value)}
                    size="small"
                  >
                    {group.members.map((m) => (
                      <MenuItem key={m.id} value={m.id}>
                        {m.name}
                      </MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    select
                    label="Split"
                    value={splitMode}
                    onChange={(e) => setSplitMode(e.target.value as SplitMode)}
                    size="small"
                  >
                    <MenuItem value="even">Evenly</MenuItem>
                    <MenuItem value="exact">Exact amounts</MenuItem>
                  </TextField>
                </Stack>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Split among
                  </Typography>
                  <Stack spacing={0.5}>
                    {group.members.map((m) => (
                      <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }} key={m.id}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={participantIds.has(m.id)}
                              onChange={() => toggleParticipant(m.id)}
                            />
                          }
                          label={m.name}
                        />
                        {splitMode === 'exact' && participantIds.has(m.id) && (
                          <TextField
                            size="small"
                            placeholder="0.00"
                            value={shares[m.id] ?? ''}
                            onChange={(e) =>
                              setShares((prev) => ({ ...prev, [m.id]: e.target.value }))
                            }
                            sx={{ width: 90 }}
                          />
                        )}
                      </Stack>
                    ))}
                  </Stack>
                </Box>
                <Button type="submit" variant="contained" sx={{ alignSelf: 'flex-start' }}>
                  Add expense
                </Button>
                {expenseError && <Alert severity="error">{expenseError}</Alert>}
              </Stack>
            </Box>
          )}

          {group.expenses.length > 0 && (
            <Table size="small" sx={{ mt: 2 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Description</TableCell>
                  <TableCell>Paid by</TableCell>
                  <TableCell align="right">Amount</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {group.expenses.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell>{e.description}</TableCell>
                    <TableCell>{memberName_(e.payer_id)}</TableCell>
                    <TableCell align="right">{formatCents(e.amount_cents)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Container>
  )
}

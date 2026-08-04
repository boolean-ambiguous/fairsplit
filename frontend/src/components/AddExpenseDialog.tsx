import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Radio,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { api, ApiError } from '../api/client'
import type { Expense, GroupDetail, SplitMode } from '../api/types'
import { formatCurrency } from '../money'
import PhotoUpload from './PhotoUpload'

interface Props {
  open: boolean
  group: GroupDetail
  myMemberId: string | null
  editing: Expense | null
  onClose: () => void
  onSaved: () => void
}

const today = () => new Date().toISOString().slice(0, 10)

export default function AddExpenseDialog({ open, group, myMemberId, editing, onClose, onSaved }: Props) {
  const [step, setStep] = useState<1 | 2>(1)
  const [desc, setDesc] = useState('')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState(today())
  const [paidBy, setPaidBy] = useState(myMemberId ?? group.members[0]?.id ?? '')
  const [notes, setNotes] = useState('')
  const [receipt, setReceipt] = useState<string | null>(null)
  const [splitMode, setSplitMode] = useState<SplitMode>('even')
  const [involved, setInvolved] = useState<Set<string>>(new Set(group.members.map((m) => m.id)))
  const [customIncluded, setCustomIncluded] = useState<Record<string, boolean>>({})
  const [customAmounts, setCustomAmounts] = useState<Record<string, string>>({})
  const [step1Error, setStep1Error] = useState<string | null>(null)
  const [step2Error, setStep2Error] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    setStep(1)
    setStep1Error(null)
    setStep2Error(null)
    if (editing) {
      setDesc(editing.description)
      setAmount((editing.amount_cents / 100).toFixed(2))
      setDate(editing.date)
      setPaidBy(editing.payer_id)
      setNotes(editing.notes ?? '')
      setReceipt(editing.receipt_data_url)
      setSplitMode(editing.split_mode)
      if (editing.split_mode === 'even') {
        setInvolved(new Set(editing.participant_ids))
        setCustomIncluded(Object.fromEntries(group.members.map((m) => [m.id, false])))
        setCustomAmounts({})
      } else {
        setInvolved(new Set(group.members.map((m) => m.id)))
        setCustomIncluded(
          Object.fromEntries(group.members.map((m) => [m.id, (editing.shares[m.id] ?? 0) > 0])),
        )
        setCustomAmounts(
          Object.fromEntries(
            Object.entries(editing.shares).map(([id, amt]) => [id, (amt / 100).toFixed(2)]),
          ),
        )
      }
    } else {
      setDesc('')
      setAmount('')
      setDate(today())
      setPaidBy(myMemberId ?? group.members[0]?.id ?? '')
      setNotes('')
      setReceipt(null)
      setSplitMode('even')
      setInvolved(new Set(group.members.map((m) => m.id)))
      setCustomIncluded(Object.fromEntries(group.members.map((m) => [m.id, true])))
      setCustomAmounts({})
    }
  }, [open, editing, group.members, myMemberId])

  const toggleInvolved = (id: string) => {
    setInvolved((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleCustom = (id: string) => {
    setCustomIncluded((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const goToStep2 = () => {
    if (!desc.trim() || !(Number(amount) > 0)) {
      setStep1Error('Give it a description and an amount above zero.')
      return
    }
    setStep1Error(null)
    setStep(2)
  }

  const totalCents = Math.round((Number(amount) || 0) * 100)
  const customSum = group.members.reduce(
    (sum, m) => (customIncluded[m.id] ? sum + Math.round((Number(customAmounts[m.id]) || 0) * 100) : sum),
    0,
  )
  const customRemaining = totalCents - customSum

  const handleSave = async () => {
    setStep2Error(null)
    if (splitMode === 'even' && involved.size < 1) {
      setStep2Error('Pick at least one person to split with.')
      return
    }
    if (splitMode === 'exact') {
      const debtors = group.members.filter(
        (m) => customIncluded[m.id] && m.id !== paidBy && Number(customAmounts[m.id]) > 0,
      )
      if (debtors.length < 1) {
        setStep2Error('Pick at least one other person and enter what they owe.')
        return
      }
      if (customRemaining !== 0) {
        setStep2Error(`Amounts must add up to the total (${formatCurrency(totalCents, group.currency)}).`)
        return
      }
    }

    setSubmitting(true)
    try {
      const body = {
        description: desc,
        amount,
        date,
        payer_id: paidBy,
        split_mode: splitMode,
        participant_ids:
          splitMode === 'even'
            ? Array.from(involved)
            : group.members.filter((m) => customIncluded[m.id] && Number(customAmounts[m.id]) > 0).map((m) => m.id),
        exact_shares:
          splitMode === 'exact'
            ? Object.fromEntries(
                group.members
                  .filter((m) => customIncluded[m.id] && Number(customAmounts[m.id]) > 0)
                  .map((m) => [m.id, customAmounts[m.id]]),
              )
            : undefined,
        notes: notes || null,
        receipt_data_url: receipt,
      }
      if (editing) {
        await api.updateExpense(group.id, editing.id, body)
      } else {
        await api.addExpense(group.id, body)
      }
      onSaved()
    } catch (err) {
      if (err instanceof ApiError) setStep2Error(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5, fontSize: 14, color: 'text.secondary' }}>
        <IconButton
          onClick={onClose}
          size="small"
          sx={{ border: 1, borderColor: 'divider', borderRadius: '8px', width: 32, height: 32 }}
        >
          ✕
        </IconButton>
        Step {step} of 2
      </DialogTitle>
      <DialogContent>
        {step === 1 ? (
          <Stack spacing={2}>
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              What's the expense?
            </Typography>
            <TextField
              label="Description"
              placeholder="e.g. Dinner at the pier"
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              fullWidth
            />
            <Stack direction="row" spacing={1.5}>
              <TextField
                label={`Amount (${group.currency})`}
                placeholder="0.00"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                sx={{ flex: 2 }}
              />
              <TextField
                label="Date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                slotProps={{ inputLabel: { shrink: true }, htmlInput: { max: today() } }}
                sx={{ flex: 1 }}
              />
            </Stack>
            <TextField select label="Paid by" value={paidBy} onChange={(e) => setPaidBy(e.target.value)} fullWidth>
              {group.members.map((m) => (
                <MenuItem key={m.id} value={m.id}>
                  {m.id === myMemberId ? 'You' : m.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Notes (optional)"
              placeholder="Anything worth remembering about this one"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              multiline
              minRows={2}
              fullWidth
            />
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                Receipt (optional)
              </Typography>
              <PhotoUpload value={receipt} onChange={setReceipt} shape="rounded" width="100%" height={120} label="Drop a receipt photo" />
            </Box>
            {step1Error && (
              <Typography color="error" variant="body2" sx={{ textAlign: 'center' }}>
                {step1Error}
              </Typography>
            )}
            <Button variant="outlined" size="large" onClick={goToStep2}>
              Next: choose a split
            </Button>
          </Stack>
        ) : (
          <Stack spacing={2}>
            <Typography variant="h6" sx={{ fontWeight: 500 }}>
              How should this be split?
            </Typography>
            <Stack spacing={1}>
              {(
                [
                  { key: 'even' as const, label: 'Split it equally', sub: 'Everyone selected pays the same even share.' },
                  { key: 'exact' as const, label: 'Split by amount', sub: 'Choose who owes what — works for any number of people.' },
                ]
              ).map((opt) => (
                <Stack
                  key={opt.key}
                  direction="row"
                  spacing={1.25}
                  onClick={() => setSplitMode(opt.key)}
                  sx={{
                    p: 1.25,
                    borderRadius: '8px',
                    bgcolor: 'background.paper',
                    cursor: 'pointer',
                    border: '1px solid',
                    borderColor: splitMode === opt.key ? 'primary.main' : 'transparent',
                  }}
                >
                  <Radio checked={splitMode === opt.key} size="small" sx={{ p: 0, mt: 0.25 }} />
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {opt.label}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {opt.sub}
                    </Typography>
                  </Box>
                </Stack>
              ))}
            </Stack>

            {splitMode === 'even' ? (
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                  Who's splitting this?
                </Typography>
                <Stack spacing={0.5}>
                  {group.members.map((m) => (
                    <Stack
                      key={m.id}
                      direction="row"
                      spacing={1.25}
                      onClick={() => toggleInvolved(m.id)}
                      sx={{ p: 1, borderRadius: '8px', bgcolor: 'background.paper', cursor: 'pointer', alignItems: 'center' }}
                    >
                      <Checkbox checked={involved.has(m.id)} size="small" sx={{ p: 0 }} />
                      <Typography variant="body2">{m.id === myMemberId ? 'You' : m.name}</Typography>
                    </Stack>
                  ))}
                </Stack>
              </Box>
            ) : (
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                  Who owes how much?
                </Typography>
                <Stack spacing={0.75}>
                  {group.members.map((m) => (
                    <Stack
                      key={m.id}
                      direction="row"
                      spacing={1.25}
                      sx={{ p: 1, borderRadius: '8px', bgcolor: 'background.paper', alignItems: 'center' }}
                    >
                      <Checkbox checked={!!customIncluded[m.id]} onChange={() => toggleCustom(m.id)} size="small" sx={{ p: 0 }} />
                      <Typography variant="body2" sx={{ flex: 1, cursor: 'pointer' }} onClick={() => toggleCustom(m.id)}>
                        {m.id === myMemberId ? 'You' : m.name}
                      </Typography>
                      <TextField
                        size="small"
                        type="number"
                        placeholder="0.00"
                        disabled={!customIncluded[m.id]}
                        value={customAmounts[m.id] ?? ''}
                        onChange={(e) => setCustomAmounts((prev) => ({ ...prev, [m.id]: e.target.value }))}
                        sx={{ width: 90 }}
                        slotProps={{ htmlInput: { style: { textAlign: 'right' } } }}
                      />
                    </Stack>
                  ))}
                </Stack>
                <Typography
                  variant="caption"
                  sx={{ display: 'block', textAlign: 'right', mt: 0.5 }}
                  color={customRemaining === 0 ? 'success.main' : 'text.secondary'}
                >
                  {customRemaining === 0
                    ? 'Amounts add up ✓'
                    : `${formatCurrency(Math.abs(customRemaining), group.currency)} ${
                        customRemaining > 0 ? 'left to assign' : 'over the total'
                      }`}
                </Typography>
              </Box>
            )}

            <Stack direction="row" spacing={1.5}>
              <Button variant="outlined" color="inherit" sx={{ flex: 1 }} onClick={() => setStep(1)}>
                Back
              </Button>
              <Button variant="outlined" sx={{ flex: 2 }} onClick={handleSave} disabled={submitting}>
                {editing ? 'Save changes' : 'Save expense'}
              </Button>
            </Stack>
            {step2Error && (
              <Typography color="error" variant="body2" sx={{ textAlign: 'center' }}>
                {step2Error}
              </Typography>
            )}
          </Stack>
        )}
      </DialogContent>
    </Dialog>
  )
}

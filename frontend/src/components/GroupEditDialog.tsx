import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { api, ApiError } from '../api/client'
import { CURRENCIES, type Currency, type GroupDetail } from '../api/types'
import PhotoUpload from './PhotoUpload'

interface Props {
  open: boolean
  group: GroupDetail
  onClose: () => void
  onSaved: () => void
}

interface MemberRow {
  id: string | null
  name: string
}

export default function GroupEditDialog({ open, group, onClose, onSaved }: Props) {
  const [name, setName] = useState(group.name)
  const [currency, setCurrency] = useState<Currency>(group.currency)
  const [photo, setPhoto] = useState<string | null>(group.photo_data_url)
  const [members, setMembers] = useState<MemberRow[]>(
    group.members.map((m) => ({ id: m.id, name: m.name })),
  )
  const [newInvites, setNewInvites] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!open) return
    setName(group.name)
    setCurrency(group.currency)
    setPhoto(group.photo_data_url)
    setMembers(group.members.map((m) => ({ id: m.id, name: m.name })))
    setNewInvites([])
    setError(null)
  }, [open, group])

  const handleSubmit = async () => {
    setError(null)
    setSubmitting(true)
    try {
      await api.updateGroup(group.id, { name, currency, photo_data_url: photo })
      for (const row of members) {
        const original = group.members.find((m) => m.id === row.id)
        if (original && row.name.trim() && row.name.trim() !== original.name) {
          await api.renameMember(group.id, row.id!, row.name.trim())
        }
      }
      for (const invite of newInvites) {
        if (invite.trim()) await api.addMember(group.id, invite.trim())
      }
      onSaved()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const removeMember = async (row: MemberRow) => {
    if (!row.id) return
    setError(null)
    try {
      await api.removeMember(group.id, row.id)
      setMembers((rows) => rows.filter((r) => r.id !== row.id))
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle sx={{ fontSize: 20, fontWeight: 500 }}>Edit group</DialogTitle>
      <DialogContent>
        <Stack spacing={2.25} sx={{ pt: 0.5 }}>
          <PhotoUpload value={photo} onChange={setPhoto} shape="circle" width={64} height={64} />
          <TextField label="Group name" value={name} onChange={(e) => setName(e.target.value)} fullWidth />
          <TextField
            select
            label="Default currency"
            value={currency}
            onChange={(e) => setCurrency(e.target.value as Currency)}
            fullWidth
          >
            {CURRENCIES.map((c) => (
              <MenuItem key={c} value={c}>
                {c}
              </MenuItem>
            ))}
          </TextField>
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              Members
            </Typography>
            <Stack spacing={1}>
              {members.map((row, i) => (
                <Stack direction="row" spacing={1} key={row.id ?? i}>
                  <TextField
                    size="small"
                    value={row.name}
                    onChange={(e) =>
                      setMembers((rows) => rows.map((r, j) => (j === i ? { ...r, name: e.target.value } : r)))
                    }
                    sx={{ flex: 1 }}
                  />
                  <IconButton size="small" onClick={() => removeMember(row)}>
                    ✕
                  </IconButton>
                </Stack>
              ))}
              {newInvites.map((value, i) => (
                <Stack direction="row" spacing={1} key={`new-${i}`}>
                  <TextField
                    size="small"
                    placeholder="Name"
                    value={value}
                    onChange={(e) =>
                      setNewInvites((rows) => rows.map((r, j) => (j === i ? e.target.value : r)))
                    }
                    sx={{ flex: 1 }}
                  />
                  <IconButton size="small" onClick={() => setNewInvites((rows) => rows.filter((_, j) => j !== i))}>
                    ✕
                  </IconButton>
                </Stack>
              ))}
            </Stack>
            <Button size="small" onClick={() => setNewInvites((rows) => [...rows, ''])} sx={{ mt: 1 }}>
              + Add another person
            </Button>
          </Box>
          {error && (
            <Typography color="error" variant="body2">
              {error}
            </Typography>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="outlined" onClick={handleSubmit} disabled={submitting || !name.trim()}>
          Save changes
        </Button>
      </DialogActions>
    </Dialog>
  )
}

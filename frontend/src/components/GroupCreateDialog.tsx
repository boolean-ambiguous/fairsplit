import { useState } from 'react'
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
import { CURRENCIES, type Currency } from '../api/types'
import PhotoUpload from './PhotoUpload'

interface InviteRow {
  name: string
  email: string
}

interface Props {
  open: boolean
  onClose: () => void
  onCreated: (groupId: string) => void
}

const EMPTY_ROW: InviteRow = { name: '', email: '' }

export default function GroupCreateDialog({ open, onClose, onCreated }: Props) {
  const [name, setName] = useState('')
  const [currency, setCurrency] = useState<Currency>('USD')
  const [photo, setPhoto] = useState<string | null>(null)
  const [invites, setInvites] = useState<InviteRow[]>([{ ...EMPTY_ROW }])
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const reset = () => {
    setName('')
    setCurrency('USD')
    setPhoto(null)
    setInvites([{ ...EMPTY_ROW }])
    setError(null)
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  const handleSubmit = async () => {
    setError(null)
    setSubmitting(true)
    try {
      const group = await api.createGroup({
        name,
        currency,
        photo_data_url: photo,
        invites: invites
          .filter((i) => i.name.trim())
          .map((i) => ({ name: i.name.trim(), email: i.email.trim() || undefined })),
      })
      reset()
      onCreated(group.id)
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="xs">
      <DialogTitle sx={{ fontSize: 20, fontWeight: 500 }}>Start a new group</DialogTitle>
      <DialogContent>
        <Stack spacing={2.25} sx={{ pt: 0.5 }}>
          <PhotoUpload value={photo} onChange={setPhoto} shape="circle" width={64} height={64} />
          <TextField
            label="Group name"
            placeholder="e.g. Ski Trip 2027"
            value={name}
            onChange={(e) => setName(e.target.value)}
            fullWidth
          />
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
              Invite people
            </Typography>
            <Stack spacing={1}>
              {invites.map((row, i) => (
                <Stack direction="row" spacing={1} key={i}>
                  <TextField
                    size="small"
                    placeholder="Name"
                    value={row.name}
                    onChange={(e) =>
                      setInvites((rows) => rows.map((r, j) => (j === i ? { ...r, name: e.target.value } : r)))
                    }
                    sx={{ flex: 1 }}
                  />
                  <TextField
                    size="small"
                    placeholder="Email"
                    value={row.email}
                    onChange={(e) =>
                      setInvites((rows) => rows.map((r, j) => (j === i ? { ...r, email: e.target.value } : r)))
                    }
                    sx={{ flex: 1 }}
                  />
                  <IconButton size="small" onClick={() => setInvites((rows) => rows.filter((_, j) => j !== i))}>
                    ✕
                  </IconButton>
                </Stack>
              ))}
            </Stack>
            <Button size="small" onClick={() => setInvites((rows) => [...rows, { ...EMPTY_ROW }])} sx={{ mt: 1 }}>
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
        <Button onClick={handleClose}>Cancel</Button>
        <Button variant="outlined" onClick={handleSubmit} disabled={submitting || !name.trim()}>
          Create group
        </Button>
      </DialogActions>
    </Dialog>
  )
}

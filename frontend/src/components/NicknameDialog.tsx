import { useState } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  TextField,
} from '@mui/material'

interface Props {
  open: boolean
  initialValue: string
  onSave: (nickname: string) => void
}

export default function NicknameDialog({ open, initialValue, onSave }: Props) {
  const [value, setValue] = useState(initialValue)

  const handleSave = (event: React.FormEvent) => {
    event.preventDefault()
    const trimmed = value.trim()
    if (trimmed) onSave(trimmed)
  }

  return (
    <Dialog open={open}>
      <DialogTitle>Which member are you?</DialogTitle>
      <Box component="form" onSubmit={handleSave}>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            FairSplit has no login — enter the name you use in your groups so the
            dashboard can show your balances. This stays on this device only.
          </DialogContentText>
          <TextField
            autoFocus
            fullWidth
            label="Your name"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button type="submit" variant="contained" disabled={!value.trim()}>
            Save
          </Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Container, InputAdornment, TextField, Typography } from '@mui/material'
import { api, ApiError } from '../api/client'
import { useAuth } from './AuthContext'

export default function HandlePage() {
  const navigate = useNavigate()
  const { setUser } = useAuth()
  const [handle, setHandle] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const user = await api.setHandle(handle)
      setUser(user)
      navigate('/', { replace: true })
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Container
      maxWidth="xs"
      sx={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', justifyContent: 'center', py: 6 }}
    >
      <Typography variant="overline" color="primary" sx={{ letterSpacing: '0.1em' }}>
        One more thing
      </Typography>
      <Typography variant="h5" sx={{ fontWeight: 500, letterSpacing: '-0.02em', mb: 1.5 }}>
        Pick a handle
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Friends can find you by this handle when adding you to a group.
      </Typography>
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          label="Handle"
          placeholder="jordan_lee"
          value={handle}
          onChange={(e) => setHandle(e.target.value.toLowerCase())}
          slotProps={{ input: { startAdornment: <InputAdornment position="start">@</InputAdornment> } }}
          fullWidth
          autoFocus
        />
        {error && (
          <Typography color="error" variant="body2">
            {error}
          </Typography>
        )}
        <Button type="submit" variant="outlined" size="large" disabled={submitting || !handle.trim()}>
          Continue
        </Button>
      </Box>
    </Container>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Container, TextField, Typography } from '@mui/material'
import { api, ApiError } from '../api/client'

export default function SignupPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await api.signup(email)
      navigate(`/verify?email=${encodeURIComponent(email.trim())}`)
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
        FairSplit
      </Typography>
      <Typography variant="h4" sx={{ fontWeight: 500, letterSpacing: '-0.02em', mb: 1.5 }}>
        Split bills, not the friendships.
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Enter your email and we'll send a magic link so you can get started. No password to
        remember.
      </Typography>
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          label="Email address"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          fullWidth
          autoFocus
        />
        {error && (
          <Typography color="error" variant="body2">
            {error}
          </Typography>
        )}
        <Button type="submit" variant="outlined" size="large" disabled={submitting || !email.trim()}>
          Send my magic link
        </Button>
      </Box>
    </Container>
  )
}

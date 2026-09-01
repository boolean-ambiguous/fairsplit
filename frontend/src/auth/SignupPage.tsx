import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Container,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { api, ApiError } from '../api/client'
import { useAuth } from './AuthContext'

type Mode = 'magic-link' | 'password'

export default function SignupPage() {
  const navigate = useNavigate()
  const { setUser } = useAuth()
  const [mode, setMode] = useState<Mode>('magic-link')
  const [email, setEmail] = useState('')
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleMagicLinkSubmit = async () => {
    await api.signup(email)
    navigate(`/verify?email=${encodeURIComponent(email.trim())}`)
  }

  const handlePasswordSubmit = async () => {
    const user = await api.login(identifier, password)
    setUser(user)
    navigate(user.name ? (user.handle ? '/' : '/handle') : '/name', { replace: true })
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (mode === 'magic-link') await handleMagicLinkSubmit()
      else await handlePasswordSubmit()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const canSubmit = mode === 'magic-link' ? Boolean(email.trim()) : Boolean(identifier.trim() && password)

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
        {mode === 'magic-link'
          ? "Enter your email and we'll send a magic link so you can get started. No password to remember."
          : 'Sign in with your email or username and password.'}
      </Typography>
      <ToggleButtonGroup
        value={mode}
        exclusive
        fullWidth
        size="small"
        onChange={(_, value: Mode | null) => {
          if (!value) return
          setMode(value)
          setError(null)
        }}
        sx={{ mb: 2 }}
      >
        <ToggleButton value="magic-link">Magic link</ToggleButton>
        <ToggleButton value="password">Password</ToggleButton>
      </ToggleButtonGroup>
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {mode === 'magic-link' ? (
          <TextField
            label="Email address"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            autoFocus
          />
        ) : (
          <>
            <TextField
              label="Email or username"
              placeholder="you@example.com"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              fullWidth
              autoFocus
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
            />
          </>
        )}
        {error && (
          <Typography color="error" variant="body2">
            {error}
          </Typography>
        )}
        <Button type="submit" variant="outlined" size="large" disabled={submitting || !canSubmit}>
          {mode === 'magic-link' ? 'Send my magic link' : 'Log in'}
        </Button>
      </Box>
    </Container>
  )
}

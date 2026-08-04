import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Box, Button, CircularProgress, Container, Typography } from '@mui/material'
import { api, ApiError } from '../api/client'
import { useAuth } from './AuthContext'

export default function VerifyPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { setUser } = useAuth()
  const email = params.get('email') ?? ''
  const token = params.get('token')
  const [status, setStatus] = useState<'pending' | 'verifying' | 'error'>(
    token ? 'verifying' : 'pending',
  )
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return
    api
      .verify(token)
      .then((user) => {
        setUser(user)
        navigate(user.name ? '/' : '/name', { replace: true })
      })
      .catch((err) => {
        setStatus('error')
        setError(err instanceof ApiError ? err.message : 'This link is invalid or has expired.')
      })
  }, [token, setUser, navigate])

  return (
    <Container
      maxWidth="xs"
      sx={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', justifyContent: 'center', py: 6 }}
    >
      <Typography variant="overline" color="primary" sx={{ letterSpacing: '0.1em' }}>
        Check your inbox
      </Typography>
      {status === 'verifying' ? (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
          <CircularProgress size={20} />
          <Typography>Confirming your link…</Typography>
        </Box>
      ) : (
        <>
          <Typography variant="h5" sx={{ fontWeight: 500, letterSpacing: '-0.02em', mb: 1.5 }}>
            {email ? `We sent a link to ${email}` : 'Check your email for a magic link'}
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>
            Click it to confirm the email is really yours. (No email provider is configured in
            this environment — check the server's console output for the link instead.)
          </Typography>
          {status === 'error' && (
            <Typography color="error" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}
          <Button variant="text" onClick={() => navigate('/signup')} sx={{ alignSelf: 'flex-start' }}>
            Use a different email
          </Button>
        </>
      )}
    </Container>
  )
}

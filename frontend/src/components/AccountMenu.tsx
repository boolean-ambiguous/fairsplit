import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Avatar,
  Box,
  Divider,
  IconButton,
  InputAdornment,
  Menu,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { api, ApiError } from '../api/client'
import type { Theme } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { initials } from '../money'

export default function AccountMenu() {
  const navigate = useNavigate()
  const { user, setUser } = useAuth()
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)
  const [handle, setHandle] = useState(user?.handle ?? '')
  const [handleError, setHandleError] = useState<string | null>(null)

  if (!user) return null

  const handleTheme = async (theme: Theme) => {
    setUser({ ...user, theme })
    await api.updateMe({ theme })
  }

  const saveHandle = async () => {
    setHandleError(null)
    if (handle.trim() === (user.handle ?? '')) return
    try {
      const updated = await api.updateMe({ handle: handle.trim() })
      setUser(updated)
      setHandle(updated.handle ?? '')
    } catch (err) {
      if (err instanceof ApiError) setHandleError(err.message)
      setHandle(user.handle ?? '')
    }
  }

  const handleLogout = async () => {
    await api.logout()
    setUser(null)
    navigate('/signup', { replace: true })
  }

  return (
    <Box sx={{ flex: 'none' }}>
      <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} size="small">
        <Avatar sx={{ width: 32, height: 32, fontSize: 13, bgcolor: '#423a6a', color: '#e7e5fe' }}>
          {initials(user.name ?? '')}
        </Avatar>
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Box sx={{ px: 1.5, pt: 0.5, pb: 1, minWidth: 220 }}>
          <Typography variant="caption" color="text.secondary">
            {user.name}
          </Typography>
          <Box sx={{ mt: 1.5 }}>
            <Typography variant="body2" sx={{ mb: 0.75 }}>
              Handle
            </Typography>
            <TextField
              size="small"
              fullWidth
              value={handle}
              onChange={(e) => setHandle(e.target.value.toLowerCase())}
              onBlur={saveHandle}
              slotProps={{ input: { startAdornment: <InputAdornment position="start">@</InputAdornment> } }}
            />
            {handleError && (
              <Typography variant="caption" color="error" sx={{ display: 'block', mt: 0.5 }}>
                {handleError}
              </Typography>
            )}
          </Box>
          <Box sx={{ mt: 1.5 }}>
            <Typography variant="body2" sx={{ mb: 0.75 }}>
              Appearance
            </Typography>
            <ToggleButtonGroup
              value={user.theme}
              exclusive
              fullWidth
              size="small"
              onChange={(_, value: Theme | null) => value && handleTheme(value)}
            >
              <ToggleButton value="system">System</ToggleButton>
              <ToggleButton value="light">Light</ToggleButton>
              <ToggleButton value="dark">Dark</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </Box>
        <Divider />
        <Box sx={{ px: 1.5, py: 1 }} onClick={handleLogout} style={{ cursor: 'pointer' }}>
          <Typography variant="body2">Log out</Typography>
        </Box>
      </Menu>
    </Box>
  )
}

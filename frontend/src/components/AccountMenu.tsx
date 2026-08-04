import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Avatar,
  Box,
  Divider,
  IconButton,
  Menu,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { initials } from '../money'

export default function AccountMenu() {
  const navigate = useNavigate()
  const { user, setUser } = useAuth()
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)

  if (!user) return null

  const handleTheme = async (theme: 'dark' | 'light') => {
    setUser({ ...user, theme })
    await api.updateMe({ theme })
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
        <Box sx={{ px: 1.5, pt: 0.5, pb: 1, minWidth: 200 }}>
          <Typography variant="caption" color="text.secondary">
            {user.name}
          </Typography>
          <Box sx={{ mt: 1.5 }}>
            <Typography variant="body2" sx={{ mb: 0.75 }}>
              Appearance
            </Typography>
            <ToggleButtonGroup
              value={user.theme}
              exclusive
              fullWidth
              size="small"
              onChange={(_, value: 'dark' | 'light' | null) => value && handleTheme(value)}
            >
              <ToggleButton value="dark">Dark</ToggleButton>
              <ToggleButton value="light">Light</ToggleButton>
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

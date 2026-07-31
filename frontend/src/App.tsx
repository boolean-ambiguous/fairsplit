import { useMemo } from 'react'
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import { CssBaseline, ThemeProvider, useMediaQuery } from '@mui/material'
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material'
import { buildTheme } from './theme'
import Dashboard from './pages/Dashboard'
import GroupList from './pages/GroupList'
import GroupDetail from './pages/GroupDetail'

function App() {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)')
  const theme = useMemo(() => buildTheme(prefersDark ? 'dark' : 'light'), [prefersDark])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AppBar position="static" color="transparent" elevation={0}>
          <Toolbar>
            <Typography
              variant="h6"
              component={Link}
              to="/"
              color="primary"
              sx={{ fontWeight: 700, textDecoration: 'none', flexGrow: 1 }}
            >
              FairSplit
            </Typography>
            <Box>
              <Button component={Link} to="/groups">
                Groups
              </Button>
            </Box>
          </Toolbar>
        </AppBar>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/groups" element={<GroupList />} />
          <Route path="/groups/:groupId" element={<GroupDetail />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App

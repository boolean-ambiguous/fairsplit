import { useMemo } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { CssBaseline, ThemeProvider, useMediaQuery } from '@mui/material'
import { AppBar, Toolbar, Typography } from '@mui/material'
import { buildTheme } from './theme'
import GroupList from './pages/GroupList'
import GroupDetail from './pages/GroupDetail'

function App() {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)')
  const theme = useMemo(() => buildTheme(prefersDark ? 'dark' : 'light'), [prefersDark])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" color="transparent" elevation={0}>
        <Toolbar>
          <Typography variant="h6" component="div" color="primary" sx={{ fontWeight: 700 }}>
            FairSplit
          </Typography>
        </Toolbar>
      </AppBar>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<GroupList />} />
          <Route path="/groups/:groupId" element={<GroupDetail />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App

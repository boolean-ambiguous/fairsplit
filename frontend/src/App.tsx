import { useMemo } from 'react'
import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Box, CircularProgress, CssBaseline, ThemeProvider } from '@mui/material'
import { buildTheme } from './theme'
import { AuthProvider, useAuth } from './auth/AuthContext'
import SignupPage from './auth/SignupPage'
import VerifyPage from './auth/VerifyPage'
import NamePage from './auth/NamePage'
import Dashboard from './pages/Dashboard'
import GroupDetail from './pages/GroupDetail'
import Landing from './pages/Landing'

function Splash() {
  return (
    <Box sx={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <CircularProgress />
    </Box>
  )
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (!user) return <Navigate to="/signup" replace />
  if (!user.name) return <Navigate to="/name" replace />
  return <>{children}</>
}

function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (user && user.name) return <Navigate to="/" replace />
  return <>{children}</>
}

function NamePageGate() {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (!user) return <Navigate to="/signup" replace />
  if (user.name) return <Navigate to="/" replace />
  return <NamePage />
}

function RootRoute() {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (!user) return <Landing />
  if (!user.name) return <Navigate to="/name" replace />
  return <Dashboard />
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/signup"
        element={
          <RedirectIfAuthed>
            <SignupPage />
          </RedirectIfAuthed>
        }
      />
      <Route path="/verify" element={<VerifyPage />} />
      <Route path="/name" element={<NamePageGate />} />
      <Route path="/" element={<RootRoute />} />
      <Route
        path="/groups/:groupId"
        element={
          <RequireAuth>
            <GroupDetail />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function ThemedApp() {
  const { user } = useAuth()
  const theme = useMemo(() => buildTheme(user?.theme ?? 'dark'), [user?.theme])
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100dvh',
          bgcolor: 'background.default',
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <Box sx={{ width: '100%', maxWidth: 480, minHeight: '100dvh', position: 'relative' }}>
          <AppRoutes />
        </Box>
      </Box>
    </ThemeProvider>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ThemedApp />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App

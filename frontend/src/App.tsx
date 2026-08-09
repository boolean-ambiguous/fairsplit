import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Box, CircularProgress, CssBaseline, ThemeProvider } from '@mui/material'
import { buildTheme } from './theme'
import { AuthProvider, useAuth } from './auth/AuthContext'
import SignupPage from './auth/SignupPage'
import VerifyPage from './auth/VerifyPage'
import NamePage from './auth/NamePage'
import HandlePage from './auth/HandlePage'
import Dashboard from './pages/Dashboard'
import GroupDetail from './pages/GroupDetail'
import Landing from './pages/Landing'

function useSystemPrefersDark() {
  const [prefersDark, setPrefersDark] = useState(
    () => window.matchMedia('(prefers-color-scheme: dark)').matches,
  )
  useEffect(() => {
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    const listener = (e: MediaQueryListEvent) => setPrefersDark(e.matches)
    mql.addEventListener('change', listener)
    return () => mql.removeEventListener('change', listener)
  }, [])
  return prefersDark
}

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
  if (!user.handle) return <Navigate to="/handle" replace />
  return <>{children}</>
}

function RedirectIfAuthed({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (user && user.name && user.handle) return <Navigate to="/" replace />
  return <>{children}</>
}

function NamePageGate() {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (!user) return <Navigate to="/signup" replace />
  if (user.name) return <Navigate to={user.handle ? '/' : '/handle'} replace />
  return <NamePage />
}

function HandlePageGate() {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (!user) return <Navigate to="/signup" replace />
  if (!user.name) return <Navigate to="/name" replace />
  if (user.handle) return <Navigate to="/" replace />
  return <HandlePage />
}

function RootRoute() {
  const { user, loading } = useAuth()
  if (loading) return <Splash />
  if (!user) return <Landing />
  if (!user.name) return <Navigate to="/name" replace />
  if (!user.handle) return <Navigate to="/handle" replace />
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
      <Route path="/handle" element={<HandlePageGate />} />
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
  const prefersDark = useSystemPrefersDark()
  const mode = user?.theme && user.theme !== 'system' ? user.theme : prefersDark ? 'dark' : 'light'
  const theme = useMemo(() => buildTheme(mode), [mode])
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

import { createTheme, type PaletteMode } from '@mui/material/styles'

// Ported from the Nocturne design-system tokens (_ds/nocturne/styles.css) in
// the Claude Design handoff — same bg/surface/text/divider/accent values.
// The accent (#9184d9, a blurple) reads as "informational" rather than
// "alarming," so it — not red/green — carries both credit and debt states
// throughout the app; only lightness/weight distinguish them.
const tokens = {
  dark: {
    bg: '#161826',
    surface: '#232532',
    ink: '#e9e9ed',
    muted: '#75798c',
    muted2: '#b2b6ca',
    accent: '#9184d9',
    accentInk: '#161826',
    owed: '#d2cefd',
    owe: '#b2b6ca',
    border: 'rgba(233,233,237,0.16)',
    border2: 'rgba(233,233,237,0.10)',
  },
  light: {
    bg: '#e4e7f5',
    surface: '#f8f9fd',
    ink: '#292b31',
    muted: '#75798c',
    muted2: '#595d6c',
    accent: '#796cbf',
    accentInk: '#f8f9fd',
    owed: '#5d5294',
    owe: '#595d6c',
    border: 'rgba(41,43,49,0.14)',
    border2: 'rgba(41,43,49,0.08)',
  },
} as const

export function buildTheme(mode: PaletteMode) {
  const t = tokens[mode]
  return createTheme({
    palette: {
      mode,
      background: { default: t.bg, paper: t.surface },
      text: { primary: t.ink, secondary: t.muted2 },
      primary: { main: t.accent, contrastText: t.accentInk },
      success: { main: t.owed, contrastText: mode === 'dark' ? '#161826' : '#f8f9fd' },
      error: { main: t.owe, contrastText: mode === 'dark' ? '#161826' : '#f8f9fd' },
      divider: t.border,
    },
    shape: { borderRadius: 10 },
    typography: {
      fontFamily:
        'Inter, system-ui, -apple-system, "Segoe UI", sans-serif',
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: { textTransform: 'none', fontWeight: 500 },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: { fontWeight: 500 },
        },
      },
    },
  })
}

export const themeTokens = tokens

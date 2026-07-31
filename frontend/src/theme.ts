import { createTheme, type PaletteMode } from '@mui/material/styles'

// Token values carried forward unchanged from the archived add-design-system
// change (openspec/changes/archive/2026-07-31-add-design-system/design.md) --
// already verified against WCAG AA contrast (>=4.5:1), not re-derived here.
const tokens = {
  light: {
    bg: '#f7f7f5',
    surface: '#ffffff',
    ink: '#1f2328',
    muted: '#57606a',
    accent: '#0f766e',
    accentInk: '#ffffff',
    positive: '#15803d',
    negative: '#b91c1c',
    border: '#e5e7eb',
  },
  dark: {
    bg: '#0f1115',
    surface: '#1a1d23',
    ink: '#e8e8e6',
    muted: '#9aa4b2',
    accent: '#5eead4',
    accentInk: '#08201d',
    positive: '#4ade80',
    negative: '#fca5a5',
    border: '#2a2f3a',
  },
} as const

export function buildTheme(mode: PaletteMode) {
  const t = tokens[mode]
  return createTheme({
    palette: {
      mode,
      background: { default: t.bg, paper: t.surface },
      text: { primary: t.ink, secondary: t.muted },
      primary: { main: t.accent, contrastText: t.accentInk },
      success: { main: t.positive },
      error: { main: t.negative },
      divider: t.border,
    },
    shape: { borderRadius: 8 },
  })
}

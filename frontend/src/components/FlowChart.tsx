import { Box, ToggleButton, ToggleButtonGroup, Typography, useTheme } from '@mui/material'
import type { DashboardRange, FlowPoint } from '../api/types'
import { buildChartData } from '../chartData'

const RANGE_LABELS: Record<DashboardRange, string> = {
  '1d': '1 day',
  '5d': '5 days',
  '1mo': '1 month',
  '12mo': '12 months',
}

interface Props {
  flow: FlowPoint[]
  range: DashboardRange
  onRangeChange: (range: DashboardRange) => void
}

export default function FlowChart({ flow, range, onRangeChange }: Props) {
  const theme = useTheme()
  const snaps = flow.map((f) => ({ owed: f.owed_cents / 100, owe: f.owe_cents / 100 }))
  const { bars, baseline, segments } = buildChartData(snaps)

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 1,
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        <Typography variant="caption" color="text.secondary">
          Balance over time
        </Typography>
        <ToggleButtonGroup
          size="small"
          exclusive
          value={range}
          onChange={(_, value: DashboardRange | null) => value && onRangeChange(value)}
        >
          {(Object.keys(RANGE_LABELS) as DashboardRange[]).map((key) => (
            <ToggleButton key={key} value={key}>
              {RANGE_LABELS[key]}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>
      <svg viewBox="0 0 600 200" style={{ width: '100%', height: 'auto', display: 'block' }} preserveAspectRatio="none">
        <line x1={0} y1={baseline} x2={600} y2={baseline} stroke={theme.palette.divider} strokeWidth={1} />
        {bars.map((b, i) => (
          <g key={i}>
            <rect x={b.owedX} y={b.owedY} width={b.barW} height={b.owedH} fill="rgba(145,132,217,0.55)" />
            <rect x={b.oweX} y={b.oweY} width={b.barW} height={b.oweH} fill="rgba(180,184,199,0.5)" />
          </g>
        ))}
        {segments.map((seg, i) => (
          <polyline
            key={i}
            points={seg.pointsStr}
            fill="none"
            stroke={seg.positive ? theme.palette.success.main : theme.palette.text.secondary}
            strokeWidth={3}
          />
        ))}
      </svg>
      <Box sx={{ display: 'flex', gap: 2.25, fontSize: 12, color: 'text.secondary', flexWrap: 'wrap', mt: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box sx={{ width: 10, height: 10, borderRadius: '2px', bgcolor: 'rgba(145,132,217,0.55)' }} />
          Owed to you
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box sx={{ width: 10, height: 10, borderRadius: '2px', bgcolor: 'rgba(180,184,199,0.5)' }} />
          You owe
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box sx={{ width: 10, height: 2, bgcolor: 'text.primary' }} />
          Net
        </Box>
      </Box>
    </Box>
  )
}

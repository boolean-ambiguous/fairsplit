import { BarChart } from '@mui/x-charts/BarChart'
import { ToggleButton, ToggleButtonGroup, Typography, Box } from '@mui/material'
import type { DashboardRange, FlowPoint } from '../api/types'
import { formatCents } from '../money'

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
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Balance trend — daily net change in what you're owed, not real cash
          movement (FairSplit doesn't record repayments)
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
      <BarChart
        height={240}
        dataset={flow}
        xAxis={[{ dataKey: 'date', scaleType: 'band' }]}
        series={[
          {
            dataKey: 'net_cents',
            label: 'Balance trend',
            valueFormatter: (v: number | null) => (v == null ? '' : formatCents(v)),
          },
        ]}
      />
    </Box>
  )
}

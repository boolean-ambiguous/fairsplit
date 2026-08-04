import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Stack, Typography } from '@mui/material'
import { api } from '../api/client'
import type { Dashboard as DashboardData, DashboardRange } from '../api/types'
import { formatCents, formatCurrency, colorFor } from '../money'
import { useAuth } from '../auth/AuthContext'
import AppHeader from '../components/AppHeader'
import FlowChart from '../components/FlowChart'
import GroupCreateDialog from '../components/GroupCreateDialog'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [range, setRange] = useState<DashboardRange>('1mo')
  const [data, setData] = useState<DashboardData | null>(null)
  const [createOpen, setCreateOpen] = useState(false)

  const refresh = () => {
    api.getDashboard(range).then(setData)
  }

  useEffect(refresh, [range])

  // Cross-group total — groups can use different currencies, so this reads
  // as a plain "$" aggregate rather than any one group's real currency
  // (the same simplification the source design made).
  const summary = () => {
    if (!data) return { text: '', color: 'text.primary' as const }
    const owed = data.open_positions.filter((p) => p.net_cents > 0).reduce((s, p) => s + p.net_cents, 0)
    const owe = data.open_positions.filter((p) => p.net_cents < 0).reduce((s, p) => s - p.net_cents, 0)
    if (owed > 0 && owe > 0)
      return {
        text: `You're owed $${formatCents(owed)} and you owe $${formatCents(owe)} overall.`,
        color: 'text.primary' as const,
      }
    if (owed > 0) return { text: `You're owed $${formatCents(owed)} overall.`, color: 'success.main' as const }
    if (owe > 0) return { text: `You owe $${formatCents(owe)} overall.`, color: 'text.secondary' as const }
    return { text: "You're all settled up!", color: 'success.main' as const }
  }
  const { text: summaryText, color: summaryColor } = summary()

  return (
    <>
      <AppHeader title="Dashboard" />
      <Box sx={{ px: 2.5, pb: 12, display: 'flex', flexDirection: 'column', gap: 3.25 }}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 500, mb: 0.25 }}>
            Hey, {user?.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Here's where things stand.
          </Typography>
        </Box>

        {data && (
          <>
            <Box sx={{ bgcolor: 'background.paper', borderRadius: '14px', p: 2.25, border: 1, borderColor: 'divider' }}>
              <Typography sx={{ fontWeight: 500, mb: 1.5 }} color={summaryColor}>
                {summaryText}
              </Typography>
              <FlowChart flow={data.flow} range={range} onRangeChange={setRange} />
            </Box>

            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2.5 }}>
              <Box>
                <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 1.25 }}>
                  Open positions
                </Typography>
                {data.open_positions.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    You're all settled up! 🎉
                  </Typography>
                ) : (
                  <Stack spacing={1}>
                    {data.open_positions.map((p, i) => (
                      <Box key={i} sx={{ bgcolor: 'background.paper', borderRadius: '8px', p: 1.25 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {p.net_cents > 0
                            ? `${p.other_name} owes you ${formatCurrency(p.net_cents, p.currency)}`
                            : `You owe ${p.other_name} ${formatCurrency(-p.net_cents, p.currency)}`}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {p.group_name}
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                )}
              </Box>

              <Box>
                <Typography variant="overline" color="text.secondary" sx={{ display: 'block', mb: 1.25 }}>
                  Your groups
                </Typography>
                <Stack spacing={1} sx={{ mb: 1.25 }}>
                  {data.groups.map((g) => (
                    <Box
                      key={g.id}
                      onClick={() => navigate(`/groups/${g.id}`)}
                      sx={{
                        bgcolor: 'background.paper',
                        borderRadius: '8px',
                        p: 1.25,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.25,
                        cursor: 'pointer',
                      }}
                    >
                      <Box
                        sx={{
                          width: 34,
                          height: 34,
                          borderRadius: '8px',
                          flex: 'none',
                          bgcolor: colorFor(g.id),
                          backgroundImage: g.photo_data_url ? `url(${g.photo_data_url})` : undefined,
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                        }}
                      />
                      <Box sx={{ minWidth: 0, flex: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }} noWrap>
                          {g.name}
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Stack>
                <Button variant="outlined" fullWidth onClick={() => setCreateOpen(true)}>
                  + New group
                </Button>
              </Box>
            </Box>
          </>
        )}
      </Box>

      <GroupCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(groupId) => {
          setCreateOpen(false)
          navigate(`/groups/${groupId}`)
        }}
      />
    </>
  )
}

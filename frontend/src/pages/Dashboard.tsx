import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Container,
  List,
  ListItem,
  Stack,
  Typography,
} from '@mui/material'
import { api } from '../api/client'
import type { Dashboard as DashboardData, DashboardRange } from '../api/types'
import { formatCents } from '../money'
import NicknameDialog from '../components/NicknameDialog'
import FlowChart from '../components/FlowChart'

const NICKNAME_KEY = 'fairsplit:nickname'

export default function Dashboard() {
  const [nickname, setNickname] = useState<string | null>(() =>
    localStorage.getItem(NICKNAME_KEY),
  )
  const [dialogOpen, setDialogOpen] = useState(!nickname)
  const [range, setRange] = useState<DashboardRange>('1mo')
  const [data, setData] = useState<DashboardData | null>(null)

  useEffect(() => {
    if (!nickname) return
    api.getDashboard(nickname, range).then(setData)
  }, [nickname, range])

  const handleSaveNickname = (value: string) => {
    localStorage.setItem(NICKNAME_KEY, value)
    setNickname(value)
    setDialogOpen(false)
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <NicknameDialog
        open={dialogOpen}
        initialValue={nickname ?? ''}
        onSave={handleSaveNickname}
      />

      <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        {nickname && (
          <Stack direction="row" sx={{ alignItems: 'center' }} spacing={0.5}>
            <Typography color="text.secondary">You are: {nickname}</Typography>
            <Button size="small" onClick={() => setDialogOpen(true)}>
              Change
            </Button>
          </Stack>
        )}
      </Stack>

      {data && (
        <>
          <Card variant="outlined" sx={{ my: 2 }}>
            <CardContent>
              <FlowChart flow={data.flow} range={range} onRangeChange={setRange} />
            </CardContent>
          </Card>

          <Typography variant="h6" component="h2" sx={{ mt: 3 }}>
            Your groups
          </Typography>
          {data.groups.length === 0 ? (
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              No groups found for "{nickname}". Add yourself as a member of a
              group, or check the spelling of your name.
            </Typography>
          ) : (
            <List disablePadding>
              {data.groups.map((group) => (
                <ListItem key={group.id} disablePadding sx={{ mb: 1 }}>
                  <Card variant="outlined" sx={{ width: '100%' }}>
                    <CardActionArea component={Link} to={`/groups/${group.id}`}>
                      <CardContent>
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                          }}
                        >
                          <Typography>{group.name}</Typography>
                          {group.balance_cents > 0 && (
                            <Chip
                              size="small"
                              color="success"
                              label={`is owed ${formatCents(group.balance_cents)}`}
                            />
                          )}
                          {group.balance_cents < 0 && (
                            <Chip
                              size="small"
                              color="error"
                              label={`owes ${formatCents(-group.balance_cents)}`}
                            />
                          )}
                          {group.balance_cents === 0 && (
                            <Chip size="small" variant="outlined" label="settled up" />
                          )}
                        </Box>
                      </CardContent>
                    </CardActionArea>
                  </Card>
                </ListItem>
              ))}
            </List>
          )}
        </>
      )}
    </Container>
  )
}

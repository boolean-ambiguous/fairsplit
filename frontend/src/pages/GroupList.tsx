import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Container,
  List,
  ListItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { api, ApiError } from '../api/client'
import type { Group } from '../api/types'

export default function GroupList() {
  const [groups, setGroups] = useState<Group[]>([])
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)

  const refresh = () => {
    api.listGroups().then(setGroups)
  }

  useEffect(refresh, [])

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    try {
      await api.createGroup(name)
      setName('')
      refresh()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
    }
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Groups
      </Typography>

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Box component="form" onSubmit={handleCreate}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-end' }}>
              <TextField
                label="New group"
                placeholder="e.g. Ski trip"
                value={name}
                onChange={(e) => setName(e.target.value)}
                size="small"
                fullWidth
              />
              <Button type="submit" variant="contained">
                Create
              </Button>
            </Stack>
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        </CardContent>
      </Card>

      {groups.length === 0 ? (
        <Typography color="text.secondary">No groups yet — create one above.</Typography>
      ) : (
        <List disablePadding>
          {groups.map((group) => (
            <ListItem key={group.id} disablePadding sx={{ mb: 1 }}>
              <Card variant="outlined" sx={{ width: '100%' }}>
                <CardActionArea component={Link} to={`/groups/${group.id}`}>
                  <CardContent>
                    <Typography>{group.name}</Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </ListItem>
          ))}
        </List>
      )}
    </Container>
  )
}

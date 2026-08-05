import { useNavigate } from 'react-router-dom'
import { Box, Button, Container, Stack, Typography } from '@mui/material'

const FEATURES = [
  'Track shared expenses as you go',
  'Split them fairly, evenly or exactly',
  'See who owes what and settle up',
]

export default function Landing() {
  const navigate = useNavigate()

  return (
    <Container
      maxWidth="xs"
      sx={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', justifyContent: 'center', py: 6 }}
    >
      <Typography variant="overline" color="primary" sx={{ letterSpacing: '0.1em' }}>
        FairSplit
      </Typography>
      <Typography variant="h4" sx={{ fontWeight: 500, letterSpacing: '-0.02em', mb: 1.5 }}>
        Split bills, not the friendships.
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        A simple way for groups to track shared expenses and settle up, without the awkward math.
      </Typography>
      <Stack spacing={1} sx={{ mb: 4 }}>
        {FEATURES.map((feature) => (
          <Box key={feature} sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
            <Typography color="primary">•</Typography>
            <Typography color="text.secondary">{feature}</Typography>
          </Box>
        ))}
      </Stack>
      <Button variant="outlined" size="large" onClick={() => navigate('/signup')}>
        Get started
      </Button>
    </Container>
  )
}

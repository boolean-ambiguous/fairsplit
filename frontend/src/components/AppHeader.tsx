import { Box, IconButton, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import AccountMenu from './AccountMenu'
import { EditIcon } from './icons'

interface Props {
  title: string
  onBack?: () => void
  onEditGroup?: () => void
}

export default function AppHeader({ title, onBack, onEditGroup }: Props) {
  const navigate = useNavigate()
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.5,
        px: 2.5,
        py: 1.75,
        position: 'sticky',
        top: 0,
        bgcolor: 'background.default',
        zIndex: 5,
      }}
    >
      {onBack && (
        <IconButton
          onClick={onBack ?? (() => navigate('/'))}
          size="small"
          sx={{ border: 1, borderColor: 'divider', borderRadius: '8px', width: 32, height: 32 }}
        >
          ←
        </IconButton>
      )}
      <Typography sx={{ fontWeight: 500, fontSize: 17, mr: 'auto' }} noWrap>
        {title}
      </Typography>
      {onEditGroup && (
        <IconButton
          onClick={onEditGroup}
          title="Edit group"
          size="small"
          sx={{ border: 1, borderColor: 'divider', borderRadius: '8px', width: 32, height: 32 }}
        >
          <EditIcon />
        </IconButton>
      )}
      <AccountMenu />
    </Box>
  )
}

import { useRef } from 'react'
import { Box, Typography } from '@mui/material'

const MAX_BYTES = 1_500_000

interface Props {
  value: string | null
  onChange: (dataUrl: string | null) => void
  shape?: 'circle' | 'rounded'
  width?: number | string
  height?: number | string
  label?: string
}

export default function PhotoUpload({
  value,
  onChange,
  shape = 'circle',
  width = 64,
  height = 64,
  label = 'Photo',
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (file: File) => {
    if (file.size > MAX_BYTES) {
      window.alert('Please choose an image under 1.5MB.')
      return
    }
    const reader = new FileReader()
    reader.onload = () => onChange(reader.result as string)
    reader.readAsDataURL(file)
  }

  return (
    <Box>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) handleFile(file)
          e.target.value = ''
        }}
      />
      <Box
        onClick={() => inputRef.current?.click()}
        sx={{
          width,
          height,
          borderRadius: shape === 'circle' ? '50%' : '10px',
          border: '1px dashed',
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          overflow: 'hidden',
          bgcolor: 'background.paper',
          backgroundImage: value ? `url(${value})` : undefined,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        {!value && (
          <Typography variant="caption" color="text.secondary" sx={{ px: 1, textAlign: 'center' }}>
            {label}
          </Typography>
        )}
      </Box>
    </Box>
  )
}

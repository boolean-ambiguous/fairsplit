import { useEffect, useRef, useState } from 'react'
import { Autocomplete, TextField } from '@mui/material'
import { api } from '../api/client'
import type { UserSearchResult } from '../api/types'

export interface InviteValue {
  text: string
  userId?: string
}

interface Props {
  value: InviteValue
  onChange: (value: InviteValue) => void
}

export default function MemberSearchInput({ value, onChange }: Props) {
  const [options, setOptions] = useState<UserSearchResult[]>([])
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (value.userId || value.text.trim().length < 2) {
      setOptions([])
      return
    }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      api
        .searchUsers(value.text.trim())
        .then(setOptions)
        .catch(() => setOptions([]))
    }, 250)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [value.text, value.userId])

  return (
    <Autocomplete
      freeSolo
      size="small"
      sx={{ flex: 1 }}
      options={options}
      filterOptions={(x) => x}
      getOptionLabel={(opt) => (typeof opt === 'string' ? opt : opt.name ?? `@${opt.handle}`)}
      inputValue={value.text}
      onInputChange={(_, newText, reason) => {
        if (reason === 'input') onChange({ text: newText, userId: undefined })
      }}
      onChange={(_, selected) => {
        if (selected && typeof selected !== 'string') {
          onChange({ text: selected.name ?? `@${selected.handle}`, userId: selected.id })
        }
      }}
      renderOption={(props, opt) => (
        <li {...props} key={opt.id}>
          {opt.name ?? 'Someone'} {opt.handle && `· @${opt.handle}`}
        </li>
      )}
      renderInput={(params) => <TextField {...params} placeholder="Name or @handle" />}
    />
  )
}

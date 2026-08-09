import { useEffect, useRef, useState } from 'react'
import { Autocomplete, TextField } from '@mui/material'
import { api } from '../api/client'
import type { UserSearchResult } from '../api/types'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export interface InviteValue {
  text: string
  userId?: string
  /** Display name for an email invite (only used when isEmailInvite(value)). */
  inviteName?: string
}

interface Props {
  value: InviteValue
  onChange: (value: InviteValue) => void
}

/** True when the typed text is a bare email with no matched handle/user — the
 * signal that this row is inviting someone who may not have an account yet. */
export function isEmailInvite(value: InviteValue): boolean {
  return !value.userId && EMAIL_RE.test(value.text.trim())
}

export function toInvitePayload(value: InviteValue): {
  name: string
  email?: string
  userId?: string
} {
  const text = value.text.trim()
  if (isEmailInvite(value)) return { name: (value.inviteName ?? '').trim(), email: text }
  return { name: text, userId: value.userId }
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
    <>
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
      {isEmailInvite(value) && (
        <TextField
          size="small"
          placeholder="Their name"
          value={value.inviteName ?? ''}
          onChange={(e) => onChange({ ...value, inviteName: e.target.value })}
          sx={{ flex: 1 }}
        />
      )}
    </>
  )
}

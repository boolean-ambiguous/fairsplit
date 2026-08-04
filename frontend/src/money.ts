import { CURRENCY_SYMBOLS, type Currency } from './api/types'

export function formatCents(cents: number): string {
  const sign = cents < 0 ? '-' : ''
  const abs = Math.abs(cents)
  const dollars = Math.floor(abs / 100)
  const rem = abs % 100
  return `${sign}${dollars}.${String(rem).padStart(2, '0')}`
}

export function formatCurrency(cents: number, currency: Currency): string {
  const symbol = CURRENCY_SYMBOLS[currency] ?? '$'
  return `${symbol}${formatCents(cents)}`
}

export function initials(name: string): string {
  return (name || '?')
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

const MEMBER_COLORS = ['#5d5294', '#75798c', '#796cbf', '#423a6a', '#595d6c', '#7972a9']

function hashId(id: string): number {
  let h = 0
  for (let i = 0; i < id.length; i++) h = (Math.imul(h, 31) + id.charCodeAt(i)) | 0
  return Math.abs(h)
}

export function colorFor(id: string): string {
  return MEMBER_COLORS[hashId(id) % MEMBER_COLORS.length]
}

export const CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD'] as const
export type Currency = (typeof CURRENCIES)[number]

export const CURRENCY_SYMBOLS: Record<Currency, string> = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  CAD: '$',
  AUD: '$',
}

// ---- Auth ----

export interface User {
  id: string
  email: string
  name: string | null
  theme: 'dark' | 'light'
}

// ---- Groups / members ----

export interface Member {
  id: string
  name: string
  email: string | null
  user_id: string | null
  created_at: string
}

export interface InviteMember {
  name: string
  email?: string
}

export interface GroupCreate {
  name: string
  currency: Currency
  photo_data_url?: string | null
  invites: InviteMember[]
}

export interface GroupUpdate {
  name?: string
  currency?: Currency
  photo_data_url?: string | null
}

export interface Group {
  id: string
  name: string
  currency: Currency
  photo_data_url: string | null
  created_at: string
  member_count: number
  balance_cents: number
}

// ---- Expenses ----

export interface ExpenseHistoryChange {
  field: string
  previous: string
  updated: string
}

export interface ExpenseHistoryEntry {
  changed_by: string
  changed_at: string
  changes: ExpenseHistoryChange[]
}

export type SplitMode = 'even' | 'exact'

export interface Expense {
  id: string
  description: string
  amount_cents: number
  payer_id: string
  date: string
  notes: string | null
  receipt_data_url: string | null
  split_mode: SplitMode
  participant_ids: string[]
  shares: Record<string, number>
  created_by: string
  created_at: string
  updated_by: string | null
  updated_at: string | null
  can_delete: boolean
  history: ExpenseHistoryEntry[]
}

export interface ExpenseCreate {
  description: string
  amount: string
  date: string
  payer_id: string
  participant_ids: string[]
  split_mode: SplitMode
  exact_shares?: Record<string, string>
  notes?: string | null
  receipt_data_url?: string | null
}

// ---- Balances / settlements ----

export interface Balance {
  member_id: string
  balance_cents: number
}

export interface SuggestedPayment {
  from_member: string
  to_member: string
  amount_cents: number
}

export interface SettlementRecord {
  id: string
  from_member: string
  to_member: string
  amount_cents: number
  recorded_by: string
  settled_at: string
}

export interface SettlementCreate {
  from_member: string
  to_member: string
  amount: string
}

export interface GroupDetail {
  id: string
  name: string
  currency: Currency
  photo_data_url: string | null
  created_at: string
  members: Member[]
  expenses: Expense[]
  balances: Balance[]
  my_positions: Balance[]
  suggested_settlements: SuggestedPayment[]
  settlement_history: SettlementRecord[]
}

// ---- Dashboard ----

export type DashboardRange = '1mo' | '12mo' | 'all'

export interface DashboardGroup {
  id: string
  name: string
  currency: Currency
  photo_data_url: string | null
  last_expense_at: string | null
  balance_cents: number
}

export interface FlowPoint {
  date: string
  owed_cents: number
  owe_cents: number
}

export interface OpenPosition {
  group_id: string
  group_name: string
  currency: Currency
  other_name: string
  net_cents: number
}

export interface Dashboard {
  name: string
  groups: DashboardGroup[]
  flow: FlowPoint[]
  open_positions: OpenPosition[]
}

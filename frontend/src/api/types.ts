export interface Group {
  id: string
  name: string
  created_at: string
}

export interface Member {
  id: string
  name: string
  created_at: string
}

export interface Expense {
  id: string
  description: string
  amount_cents: number
  payer_id: string
  created_at: string
}

export interface Balance {
  member_id: string
  balance_cents: number
}

export interface Settlement {
  from_member: string
  to_member: string
  amount_cents: number
}

export interface GroupDetail extends Group {
  members: Member[]
  expenses: Expense[]
  balances: Balance[]
  settlements: Settlement[]
}

export type SplitMode = 'even' | 'exact'

export interface ExpenseCreate {
  description: string
  amount: string
  payer_id: string
  participant_ids: string[]
  split_mode: SplitMode
  exact_shares?: Record<string, string>
}

export type DashboardRange = '1d' | '5d' | '1mo' | '12mo'

export interface DashboardGroup {
  id: string
  name: string
  last_expense_at: string | null
  balance_cents: number
}

export interface FlowPoint {
  date: string
  net_cents: number
  // MUI x-charts' `dataset` prop requires an index signature on its items.
  [key: string]: unknown
}

export interface Dashboard {
  nickname: string
  groups: DashboardGroup[]
  flow: FlowPoint[]
}

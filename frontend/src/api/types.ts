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

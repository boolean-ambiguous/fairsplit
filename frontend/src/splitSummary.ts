import { formatCurrency } from './money'
import type { Currency, Expense, Member } from './api/types'

function nameFor(memberId: string, myMemberId: string | null, membersById: Record<string, Member>): string {
  if (memberId === myMemberId) return 'You'
  return membersById[memberId]?.name ?? 'Someone'
}

/** Ported from the mockup's splitTagText — a one-line human description of
 * who owes what for a given expense, personalized to the viewer. */
export function splitSummary(
  expense: Pick<Expense, 'split_mode' | 'shares' | 'payer_id'>,
  myMemberId: string | null,
  membersById: Record<string, Member>,
  currency: Currency,
): string {
  if (expense.split_mode === 'even') {
    return 'Split equally'
  }
  const debts = Object.entries(expense.shares).filter(([id, amt]) => id !== expense.payer_id && amt > 0)
  if (debts.length === 0) return 'Split by amount'
  if (debts.length === 1) {
    const [id, amt] = debts[0]
    const debtorName = nameFor(id, myMemberId, membersById)
    const verb = id === myMemberId ? 'owe' : 'owes'
    const target = expense.payer_id === myMemberId ? 'you' : nameFor(expense.payer_id, myMemberId, membersById)
    return `${debtorName} ${verb} ${target} ${formatCurrency(amt, currency)}`
  }
  return `Split by amount across ${debts.length} people`
}

export function memberDisplayName(
  memberId: string,
  myMemberId: string | null,
  membersById: Record<string, Member>,
): string {
  return nameFor(memberId, myMemberId, membersById)
}

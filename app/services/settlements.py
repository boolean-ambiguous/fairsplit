import heapq
import uuid
from typing import NamedTuple


class Payment(NamedTuple):
    from_member: uuid.UUID
    to_member: uuid.UUID
    amount_cents: int


def suggest_settlements(balances: dict[uuid.UUID, int]) -> list[Payment]:
    """Greedy plan zeroing all balances in at most len(balances) - 1 payments.

    Largest debtor pays largest creditor each round; ties break on member id
    (a total order under any comparable id type, though under random UUIDs
    the specific winner of a tie is not meaningful — see design.md for
    add-uuid-primary-keys).
    """
    # Max-heaps via negation; (amount, id) tuples make ordering deterministic.
    debtors = [(bal, mid) for mid, bal in balances.items() if bal < 0]
    creditors = [(-bal, mid) for mid, bal in balances.items() if bal > 0]
    heapq.heapify(debtors)
    heapq.heapify(creditors)

    payments: list[Payment] = []
    while debtors and creditors:
        debt, debtor = heapq.heappop(debtors)
        credit, creditor = heapq.heappop(creditors)
        amount = min(-debt, -credit)
        payments.append(Payment(debtor, creditor, amount))
        if -debt > amount:
            heapq.heappush(debtors, (debt + amount, debtor))
        if -credit > amount:
            heapq.heappush(creditors, (credit + amount, creditor))
    return payments

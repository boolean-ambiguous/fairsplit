import heapq
from typing import NamedTuple


class Payment(NamedTuple):
    from_member: int
    to_member: int
    amount_cents: int


def suggest_settlements(balances: dict[int, int]) -> list[Payment]:
    """Greedy plan zeroing all balances in at most len(balances) - 1 payments.

    Largest debtor pays largest creditor each round; ties break on member id.
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

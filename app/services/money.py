from decimal import Decimal, InvalidOperation


class MoneyError(ValueError):
    pass


def parse_amount(raw: str) -> int:
    """Parse a decimal currency string into positive integer cents."""
    try:
        value = Decimal(raw.strip())
    except InvalidOperation:
        raise MoneyError(f"Not a valid amount: {raw!r}")
    if value != value.quantize(Decimal("0.01")):
        raise MoneyError("Amounts cannot have more than two decimal places")
    cents = int(value * 100)
    if cents <= 0:
        raise MoneyError("Amount must be positive")
    return cents


def parse_share(raw: str) -> int:
    """Like parse_amount but a share may be zero; blank input counts as zero."""
    if not raw.strip():
        return 0
    try:
        value = Decimal(raw.strip())
    except InvalidOperation:
        raise MoneyError(f"Not a valid amount: {raw!r}")
    if value != value.quantize(Decimal("0.01")):
        raise MoneyError("Amounts cannot have more than two decimal places")
    cents = int(value * 100)
    if cents < 0:
        raise MoneyError("Shares cannot be negative")
    return cents


def format_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"

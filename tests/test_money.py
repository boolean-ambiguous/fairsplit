import pytest

from app.services.money import MoneyError, parse_amount, parse_share


def test_parse_amount_accepts_two_decimal_places():
    assert parse_amount("10.00") == 1000


def test_parse_amount_rejects_too_many_decimal_places():
    with pytest.raises(MoneyError):
        parse_amount("10.005")


def test_parse_amount_rejects_non_positive():
    with pytest.raises(MoneyError):
        parse_amount("0.00")


def test_parse_amount_rejects_garbage():
    with pytest.raises(MoneyError):
        parse_amount("not-a-number")


def test_parse_amount_raises_money_error_for_oversized_input_instead_of_crashing():
    # A huge digit string parses fine as a Decimal, but exceeds the default
    # 28-digit context precision on .quantize() — that must surface as a
    # MoneyError (422), not an unhandled decimal.InvalidOperation (500).
    with pytest.raises(MoneyError):
        parse_amount("1" * 50)


def test_parse_share_raises_money_error_for_oversized_input_instead_of_crashing():
    with pytest.raises(MoneyError):
        parse_share("1" * 50)


def test_parse_share_blank_is_zero():
    assert parse_share("") == 0


def test_parse_share_rejects_negative():
    with pytest.raises(MoneyError):
        parse_share("-1.00")

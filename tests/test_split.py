import pytest

from app.services.expenses import ExpenseError, split_evenly


def test_even_division():
    assert split_evenly(6000, [1, 2, 3]) == {1: 2000, 2: 2000, 3: 2000}


def test_remainder_goes_to_lowest_ids():
    assert split_evenly(10000, [1, 2, 3]) == {1: 3334, 2: 3333, 3: 3333}
    assert split_evenly(10001, [1, 2, 3]) == {1: 3334, 2: 3334, 3: 3333}


def test_remainder_is_order_independent():
    assert split_evenly(10000, [3, 1, 2]) == split_evenly(10000, [1, 2, 3])


def test_single_participant():
    assert split_evenly(999, [7]) == {7: 999}


def test_empty_participants_rejected():
    with pytest.raises(ExpenseError):
        split_evenly(1000, [])


@pytest.mark.parametrize("amount", [1, 99, 100, 101, 12345, 100000])
@pytest.mark.parametrize("n", [1, 2, 3, 7])
def test_shares_always_sum_to_total(amount, n):
    shares = split_evenly(amount, list(range(1, n + 1)))
    assert sum(shares.values()) == amount

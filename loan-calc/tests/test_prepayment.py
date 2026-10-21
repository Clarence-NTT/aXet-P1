import pytest

from loan_calc.calculator import prepayment_savings


def test_prepayment_clamps_balance_and_no_negative_and_savings_non_negative():
    p = 500_000
    annual = 9.0
    n = 60
    prepay_month = 12
    prepay_amount = 10_000_000

    res = prepayment_savings(p, annual, n, prepay_month, prepay_amount)

    assert res["new_tenure"] == prepay_month
    assert res["months_saved"] == (n - prepay_month)
    assert res["interest_saved"] >= 0


def test_prepayment_interest_saved_non_negative():
    res = prepayment_savings(800_000, 9.0, 120, 24, 200_000)
    assert res["interest_saved"] >= 0

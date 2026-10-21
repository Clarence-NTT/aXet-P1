import math

import pytest

from loan_calc.calculator import emi


def test_emi_reference_case_10L_9pct_240m():
    # Independent calculation:
    # P = 1,000,000
    # annual_rate = 9% => r = 9/1200 = 0.0075
    # n = 240
    # EMI = P*r*(1+r)^n / ((1+r)^n - 1)
    p = 1_000_000
    r = 9 / 1200
    n = 240
    f = (1 + r) ** n
    expected = p * r * f / (f - 1)
    assert emi(p, 9, n) == pytest.approx(expected, abs=1.0)


def test_emi_zero_interest():
    # r = 0 => EMI = P/n exactly
    assert emi(500_000, 0.0, 100) == pytest.approx(500_000 / 100, abs=0.01)


def test_emi_one_month():
    # For n=1, EMI = P*(1+r), with r=annual/1200
    p = 1_000_000
    r = 9 / 1200
    expected = p * (1 + r)
    assert emi(p, 9.0, 1) == pytest.approx(expected, abs=0.01)


def test_emi_large_principal_is_finite_and_positive():
    val = emi(1_000_000_000_000, 7.25, 240)
    assert math.isfinite(val)
    assert val > 0

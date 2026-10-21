import math
from datetime import date

import pytest

from loan_calc.calculator import (
    compare_offers,
    eligible_amount,
    format_inr,
    outstanding_after,
    schedule_to_csv,
    summary,
    total_interest,
    total_payment,
)


def test_total_payment_and_interest_consistency():
    p = 250_000
    annual = 9.0
    n = 36
    tp = total_payment(p, annual, n)
    ti = total_interest(p, annual, n)
    assert tp == pytest.approx(p + ti, abs=0.01)
    assert ti >= 0


def test_outstanding_after_end_of_tenure_is_zero():
    p = 100_000
    annual = 10.0
    n = 12
    assert outstanding_after(p, annual, n, n) == pytest.approx(0.0, abs=0.01)


def test_compare_offers_sorted_by_total_cost_and_fee_calculation():
    p = 1_000_000
    offers = [
        {"bank": "A", "rate": 9.0, "tenure": 240, "processing_fee_pct": 1.0},
        {"bank": "B", "rate": 8.9, "tenure": 240, "processing_fee_pct": 1.5},
        {"bank": "C", "rate": 9.1, "tenure": 240},  # no processing fee
    ]
    out = compare_offers(p, offers)

    # processing fee should be pct of principal
    bank_a = next(x for x in out if x["bank"] == "A")
    assert bank_a["processing_fee"] == pytest.approx(p * 1.0 / 100, abs=0.01)

    # list must be sorted ascending by total_cost
    total_costs = [x["total_cost"] for x in out]
    assert total_costs == sorted(total_costs)


def test_eligible_amount_zero_rate_and_negative_available():
    # available = income*foir - existing_emis
    assert eligible_amount(10_000, 20_000, 9.0, 240) == 0.0

    # at 0% rate, eligible = available * tenure
    assert eligible_amount(100_000, 0.0, 0.0, 12, foir=0.5) == pytest.approx(50_000 * 12, abs=0.01)


def test_format_inr_examples_and_negative():
    assert format_inr(123.4) == "₹123.40"
    assert format_inr(1234.0) == "₹1,234.00"
    assert format_inr(12345678.9) == "₹1,23,45,678.90"
    assert format_inr(-10) == "-₹10.00"


def test_summary_date_math_and_keys():
    s = summary(100_000, 9.0, 14, start=date(2026, 1, 15))
    # tenure 14 months from Jan 2026 -> Mar 2027
    assert s["last_emi"] == "2027-03"
    for key in [
        "principal",
        "rate",
        "tenure",
        "emi",
        "total_interest",
        "total_payment",
        "last_emi",
        "currency",
    ]:
        assert key in s


def test_schedule_to_csv_writes_file(tmp_path):
    rows = [
        {"month": 1, "emi": 100.0, "interest": 10.0, "principal": 90.0, "balance": 910.0},
        {"month": 2, "emi": 100.0, "interest": 9.1, "principal": 90.9, "balance": 819.1},
    ]
    out_path = tmp_path / "sched.csv"
    schedule_to_csv(rows, str(out_path))

    text = out_path.read_text()
    assert text.startswith("month,emi,interest,principal,balance\n")
    assert "1,100.0,10.0,90.0,910.0\n" in text
    assert "2,100.0,9.1,90.9,819.1\n" in text


def test_emi_is_finite_for_reasonable_inputs():
    # Extra sanity for float stability
    from loan_calc.calculator import emi

    val = emi(123_456_789, 13.75, 180)
    assert math.isfinite(val)
    assert val > 0

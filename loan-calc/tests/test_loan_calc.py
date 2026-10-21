import math
from datetime import date

import pytest

from loan_calc.calculator import (
    amortisation_schedule,
    compare_offers,
    eligible_amount,
    emi,
    format_inr,
    outstanding_after,
    prepayment_savings,
    schedule_to_csv,
    summary,
    total_interest,
    total_payment,
)
from loan_calc.errors import (
    InvalidPrepaymentError,
    InvalidPrincipalError,
    InvalidRateError,
    InvalidTenureError,
    LoanCalcError,
)


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


def test_schedule_one_month_row_and_balance_zero():
    # Independent calculation for 1-month loan:
    # r = annual/1200
    # interest_1 = P*r
    # emi_1 = P*(1+r)
    # principal_1 = emi_1 - interest_1 = P
    p = 1_000_000
    annual = 9.0
    r = annual / 1200
    expected_emi = p * (1 + r)
    expected_interest = p * r
    expected_principal = p

    rows = amortisation_schedule(p, annual, 1)
    assert len(rows) == 1
    row = rows[0]
    assert row["month"] == 1
    assert row["emi"] == pytest.approx(expected_emi, abs=0.01)
    assert row["interest"] == pytest.approx(expected_interest, abs=0.01)
    assert row["principal"] == pytest.approx(expected_principal, abs=0.01)
    assert row["balance"] == pytest.approx(0.0, abs=0.01)


def test_schedule_invariants_row_count_and_final_balance():
    p = 200_000
    annual = 12.0
    n = 12
    rows = amortisation_schedule(p, annual, n)
    assert len(rows) == n
    assert rows[-1]["balance"] == pytest.approx(0.0, abs=0.01)


def test_schedule_interest_formula_each_row():
    p = 150_000
    annual = 10.0
    n = 24
    r = annual / 1200

    rows = amortisation_schedule(p, annual, n)

    opening = p
    for row in rows:
        expected_interest = opening * r
        assert row["interest"] == pytest.approx(expected_interest, abs=0.01)
        opening = row["balance"]


def test_schedule_balance_strictly_decreasing_and_non_negative():
    rows = amortisation_schedule(300_000, 11.0, 36)
    balances = [row["balance"] for row in rows]
    assert all(b >= 0 for b in balances)
    assert all(balances[i + 1] < balances[i] for i in range(len(balances) - 1))


def test_schedule_sum_principal_components_approximately_principal():
    p = 100_000
    annual = 8.0
    n = 18
    rows = amortisation_schedule(p, annual, n)
    total_principal = sum(r["principal"] for r in rows)

    # Allow some tolerance due to per-month rounding.
    assert total_principal == pytest.approx(p, abs=0.5)


def test_outstanding_after_zero_months():
    assert outstanding_after(123_456, 9.0, 24, 0) == pytest.approx(123_456.0, abs=0.01)


def test_schedule_uses_emi():
    # Sanity check: each row's EMI equals the module's EMI (except potentially the last month).
    p = 250_000
    annual = 9.5
    n = 24
    expected = emi(p, annual, n)
    rows = amortisation_schedule(p, annual, n)
    for row in rows[:-1]:
        assert row["emi"] == pytest.approx(expected, abs=0.01)


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
    val = emi(123_456_789, 13.75, 180)
    assert math.isfinite(val)
    assert val > 0


def test_validation_emi_invalid_principal():
    with pytest.raises(InvalidPrincipalError):
        emi(0, 9.0, 12)
    with pytest.raises(InvalidPrincipalError):
        emi("100000", 9.0, 12)  # type: ignore[arg-type]


def test_validation_emi_invalid_rate():
    with pytest.raises(InvalidRateError):
        emi(100_000, -1.0, 12)
    with pytest.raises(InvalidRateError):
        emi(100_000, "9", 12)  # type: ignore[arg-type]


def test_validation_emi_invalid_tenure():
    with pytest.raises(InvalidTenureError):
        emi(100_000, 9.0, 0)
    with pytest.raises(InvalidTenureError):
        emi(100_000, 9.0, 12.5)  # type: ignore[arg-type]


def test_validation_outstanding_after_invalid_months_paid():
    with pytest.raises(InvalidTenureError):
        outstanding_after(100_000, 9.0, 12, -1)
    with pytest.raises(InvalidTenureError):
        outstanding_after(100_000, 9.0, 12, 1.2)  # type: ignore[arg-type]


def test_validation_prepayment_invalid_inputs():
    with pytest.raises(InvalidPrepaymentError):
        prepayment_savings(100_000, 9.0, 12, 1, -10)
    with pytest.raises(InvalidTenureError):
        prepayment_savings(100_000, 9.0, 12, 0, 10_000)
    with pytest.raises(InvalidTenureError):
        prepayment_savings(100_000, 9.0, 12, 13, 10_000)


def test_validation_compare_offers_invalid_principal():
    with pytest.raises(InvalidPrincipalError):
        compare_offers(0, [{"bank": "A", "rate": 9.0, "tenure": 12}])


def test_validation_eligible_amount_invalid_inputs():
    with pytest.raises(InvalidTenureError):
        eligible_amount(100_000, 0.0, 9.0, 0)
    with pytest.raises(InvalidRateError):
        eligible_amount(100_000, 0.0, -1.0, 12)
    with pytest.raises(LoanCalcError):
        eligible_amount("100_000", 0.0, 9.0, 12)  # type: ignore[arg-type]
    with pytest.raises(LoanCalcError):
        eligible_amount(100_000, 0.0, 9.0, 12, foir=2.0)


def test_validation_format_inr_non_numeric():
    with pytest.raises(LoanCalcError):
        format_inr("123")  # type: ignore[arg-type]


def test_validation_schedule_to_csv_path_type(tmp_path):
    rows = [{"month": 1, "emi": 1.0, "interest": 0.0, "principal": 1.0, "balance": 0.0}]
    with pytest.raises(LoanCalcError):
        schedule_to_csv(rows, tmp_path)  # type: ignore[arg-type]


def test_validation_summary_start_type():
    with pytest.raises(LoanCalcError):
        summary(100_000, 9.0, 12, start="2026-01-01")  # type: ignore[arg-type]

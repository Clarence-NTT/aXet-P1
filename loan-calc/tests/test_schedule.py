import pytest

from loan_calc.calculator import amortisation_schedule, emi


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
    from loan_calc.calculator import outstanding_after

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

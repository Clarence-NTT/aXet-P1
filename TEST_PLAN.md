# Phase 3 — Proposed test plan (loan-calc)

All currency amounts are in INR.

| Test name | Function(s) | Inputs | Expected | Derivation (independent) |
|---|---|---|---|---|
| test_emi_reference_case_10L_9pct_240m | `emi` | P=1,000,000; annual=9%; n=240 | EMI ≈ 8,997 (±1) | r = 9/1200 = 0.0075. EMI = P*r*(1+r)^n / ((1+r)^n - 1). Compute (1.0075)^240 ≈ exp(240*ln(1.0075)) ≈ exp(240*0.007472) ≈ exp(1.793) ≈ 6.01. EMI ≈ 1,000,000 * 0.0075 * 6.01 / (6.01-1) ≈ 1,000,000 * 0.045075 / 5.01 ≈ 8,996.0. Rounded ~ 8,997. |
| test_emi_zero_interest | `emi` | P=500,000; annual=0; n=100 | 5,000.00 exactly | With r=0, EMI = P/n = 500000/100 = 5000. |
| test_emi_one_month | `emi` | P=1,000,000; annual=9%; n=1 | 1,007,500.00 (±0.01) | For n=1, EMI = P*(1+r) where r=0.0075 → 1,000,000*1.0075 = 1,007,500. |
| test_schedule_one_month_row_and_balance_zero | `amortisation_schedule` | P=1,000,000; annual=9%; n=1 | 1 row; final balance 0 | Month 1 interest = P*r = 7,500; principal part = EMI-interest = 1,007,500-7,500 = 1,000,000; ending balance 0. |
| test_schedule_invariants_row_count_and_final_balance | `amortisation_schedule` | sample: P=200,000; annual=12%; n=12 | rows == 12; final balance == 0 | Definitions: schedule must have one row per month; last row should clear remaining principal (within rounding). |
| test_schedule_interest_formula_each_row | `amortisation_schedule` | P=150,000; annual=10%; n=24 | each row interest == opening_balance * r (±0.01) | r=annual/1200; interest computed per month; verify equality to within 0.01. |
| test_schedule_balance_strictly_decreasing | `amortisation_schedule` | P=300,000; annual=11%; n=36 | balance decreases each month, never negative | balance_{k+1} < balance_k and min(balance) >= 0. |
| test_schedule_sum_principal_components | `amortisation_schedule` | P=100,000; annual=8%; n=18 | sum(principal parts) ≈ P (tolerance for rounding) | Sum of principal components should equal principal (allow small rounding diff e.g. ±0.5). |
| test_outstanding_after_zero_months | `outstanding_after` | P=123,456; annual=9%; n=24; months_paid=0 | 123,456.00 | code path returns principal (rounded). |
| test_large_principal_precision | `emi` + schedule | P=1_000_000_000_000; annual=7.25%; n=240 | finite float; EMI > 0 | sanity: result is finite and positive; schedule balances not NaN/inf. |
| test_prepayment_clamps_balance_and_no_negative | `prepayment_savings` + schedule | P=500,000; annual=9%; n=60; prepay_month=12; prepay_amount huge (e.g. 10,000,000) | new_tenure == prepay_month; months_saved == original_left; savings >= 0 | if prepay >= balance, loan ends immediately after prepay month; interest saved should not be negative. |
| test_prepayment_invariant_interest_reduces | `prepayment_savings` | P=800,000; annual=9%; n=120; prepay_month=24; prepay_amount=200,000 | interest_saved >= 0 | Prepayment reduces outstanding, should not increase total interest in a “same EMI, shorter tenure” scenario. |

Notes:
- We will use `pytest.approx` with explicit tolerances for floats.
- Where we rely on “definition/invariants”, expected values are derived from the amortisation formulas (not from the module’s output).

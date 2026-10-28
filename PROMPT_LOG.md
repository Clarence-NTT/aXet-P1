# Prompt Log

Columns: `# | Phase | Prompt (summary) | AI output (summary) | Correct? | What was wrong / how it was fixed`

| # | Phase | Prompt (summary) | AI output (summary) | Correct? | What was wrong / how it was fixed |
|---:|:-----:|------------------|---------------------|:--------:|-----------------------------------|
| 1 | 1 | Initial read-through summary of suspicious areas in `calculator.py` | I stated `_monthly_rate()` was likely wrong because it rounds to 4dp, and implied the rounding was definitely a bug. | Partially | Line-by-line cross-check: `_monthly_rate()` rounding was explicitly coded in the starter. Whether it is desirable is uncertain and must be validated via tests. Fixed by documenting the behaviour under **Rounding conventions** and listing it under **Suspicious behaviour** (not as a confirmed defect). |
| 2 | 3 | Build Phase 3 test suite | I initially created multiple pytest modules (`test_emi.py`, `test_schedule.py`, `test_prepayment.py`, `test_misc.py`). | No | Requirement was to keep tests in a single Python script. Fixed by consolidating into `loan-calc/tests/test_loan_calc.py` and removing the split test files while keeping pytest discovery working. |

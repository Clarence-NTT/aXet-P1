import math
from datetime import date
from typing import Any


DEFAULT_CURRENCY = "INR"


def _monthly_rate(annual_rate: float) -> float:
    """Convert annual interest rate (percent) into a monthly fractional rate.

    The standard nominal monthly rate is: `annual_rate / 1200`.

    Notes:
        This returns the unrounded monthly rate. Rounding is applied later when
        monetary amounts are rounded to 2 decimal places.
    """
    return annual_rate / 1200


def emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Compute the Equated Monthly Instalment (EMI) for a standard amortising loan.

    Args:
        principal: Loan principal amount. Must be positive.
        annual_rate: Annual interest rate in percent (e.g. 9 for 9% p.a.).
        tenure_months: Tenure in months. Must be positive.

    Returns:
        Monthly EMI rounded to 2 decimal places.

    Raises:
        ValueError: If `tenure_months <= 0` or `principal <= 0`.

    Example:
        >>> emi(1000000, 9, 240)  # doctest: +SKIP
        8996.97
    """
    if tenure_months <= 0:
        raise ValueError("tenure must be positive")
    if principal <= 0:
        raise ValueError("principal must be positive")
    r = _monthly_rate(annual_rate)
    if r == 0:
        return round(principal / tenure_months, 2)
    f = (1 + r) ** tenure_months
    return round(principal * r * f / (f - 1), 2)


def total_payment(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Compute the total amount paid over the full tenure.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual interest rate in percent.
        tenure_months: Tenure in months.

    Returns:
        Total paid amount rounded to 2 decimal places.
    """
    return round(emi(principal, annual_rate, tenure_months) * tenure_months, 2)


def total_interest(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Compute total interest payable over the full tenure.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual interest rate in percent.
        tenure_months: Tenure in months.

    Returns:
        Total interest paid rounded to 2 decimal places.
    """
    return round(total_payment(principal, annual_rate, tenure_months) - principal, 2)


def amortisation_schedule(principal: float, annual_rate: float, tenure_months: int) -> list[dict[str, float]]:
    """Build an amortisation schedule.

    Each row contains the month number, EMI paid, interest component, principal
    component, and remaining balance after the payment.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual interest rate in percent.
        tenure_months: Tenure in months.

    Returns:
        List of rows (dicts). Monetary values are rounded to 2 decimals.
    """
    r = _monthly_rate(annual_rate)
    instalment = emi(principal, annual_rate, tenure_months)
    balance = principal
    rows = []
    for month in range(1, tenure_months + 1):
        interest = round(balance * r, 2)
        if month == tenure_months:
            # Last month: clear the remaining balance (after rounding) and adjust EMI accordingly.
            principal_part = round(balance, 2)
            instalment_amt = round(principal_part + interest, 2)
        else:
            instalment_amt = instalment
            principal_part = round(instalment - interest, 2)
        balance = round(balance - principal_part, 2)
        rows.append(
            {
                "month": month,
                "emi": instalment_amt,
                "interest": interest,
                "principal": principal_part,
                "balance": max(balance, 0.0),
            }
        )
    return rows


def outstanding_after(principal: float, annual_rate: float, tenure_months: int, months_paid: int) -> float:
    """Compute the outstanding balance after a given number of payments.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual interest rate in percent.
        tenure_months: Tenure in months.
        months_paid: Number of EMIs already paid.

    Returns:
        The remaining balance after `months_paid` payments (rounded to 2 decimals).
    """
    if months_paid <= 0:
        return round(principal, 2)
    sched = amortisation_schedule(principal, annual_rate, tenure_months)
    if months_paid > len(sched):
        return 0.0
    return sched[months_paid - 1]["balance"]


def remaining_tenure(balance: float, annual_rate: float, instalment: float) -> int:
    """Compute the remaining number of months to repay a balance for a fixed instalment.

    Notes:
        Uses the standard amortisation rearrangement (monthly compounding) to solve
        for `n` in:

            balance = instalment * (1 - (1 + r)^(-n)) / r

        where r is the monthly rate `annual_rate / 1200`.

    Args:
        balance: Outstanding principal.
        annual_rate: Annual interest rate in percent.
        instalment: Fixed monthly instalment.

    Returns:
        Remaining tenure in months, rounded up using `math.ceil`.

    Raises:
        ValueError: If `instalment` is too small to ever repay interest+principal.
    """
    r = _monthly_rate(annual_rate)
    if balance <= 0:
        return 0
    if r == 0:
        return math.ceil(balance / instalment)
    if instalment <= balance * r:
        raise ValueError("instalment too small to repay the loan")
    n = -math.log(1 - balance * r / instalment) / math.log(1 + r)
    return math.ceil(n)


def prepayment_savings(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    prepay_month: int,
    prepay_amount: float,
) -> dict[str, float]:
    """Keep the same EMI after a lump-sum prepayment and shorten the tenure.

    Args:
        principal: Original principal amount.
        annual_rate: Annual interest rate in percent.
        tenure_months: Original tenure in months.
        prepay_month: Month at which prepayment is made (expected 1-based).
        prepay_amount: Lump-sum amount paid towards the principal.

    Returns:
        A dict with keys:
        - emi
        - months_saved
        - new_tenure
        - interest_saved
        - interest_paid_before_prepayment
    """
    instalment = emi(principal, annual_rate, tenure_months)
    sched = amortisation_schedule(principal, annual_rate, tenure_months)
    balance = sched[prepay_month - 1]["balance"]
    new_balance = balance - prepay_amount
    if new_balance <= 0:
        months_left = 0
    else:
        months_left = remaining_tenure(new_balance, annual_rate, instalment)
    original_left = tenure_months - prepay_month
    interest_paid_so_far = sum(row["interest"] for row in sched[:prepay_month])
    original_interest = total_interest(principal, annual_rate, tenure_months)
    # Total interest with prepayment should compare apples-to-apples against the original
    # loan's total paid amount (principal + original_interest). A lump-sum prepayment is
    # still part of the principal repayment, so it must not be added on top of principal.
    original_total = principal + original_interest
    new_total = instalment * prepay_month + prepay_amount + instalment * months_left
    new_interest = new_total - principal
    new_interest = min(new_interest, original_interest)
    return {
        "emi": instalment,
        "months_saved": original_left - months_left,
        "new_tenure": prepay_month + months_left,
        "interest_saved": round(original_interest - new_interest, 2),
        "interest_paid_before_prepayment": round(interest_paid_so_far, 2),
    }


def compare_offers(principal: float, offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare bank loan offers by total cost.

    Args:
        principal: The principal amount assumed for all offers.
        offers: List of offers. Each offer is expected to contain:
            - bank: str
            - rate: float (annual %)
            - tenure: int (months)
            - processing_fee_pct: float (optional)

    Returns:
        Offers decorated with EMI, total_interest, processing_fee and total_cost,
        sorted by total_cost ascending.

    Notes:
        `total_cost` is computed as `total_interest + processing_fee` (it excludes
        the principal, which is constant across offers).
    """
    out = []
    for o in offers:
        e = emi(principal, o["rate"], o["tenure"])
        ti = total_interest(principal, o["rate"], o["tenure"])
        fee = o.get("processing_fee_pct", 0) * principal / 100
        out.append(
            {
                "bank": o["bank"],
                "emi": e,
                "total_interest": ti,
                "processing_fee": round(fee, 2),
                "total_cost": round(ti + fee, 2),
            }
        )
    out.sort(key=lambda x: x["total_cost"])
    return out


def eligible_amount(
    monthly_income: float,
    existing_emis: float,
    annual_rate: float,
    tenure_months: int,
    foir: float = 0.5,
) -> float:
    """Compute eligible principal amount from income and existing obligations.

    Args:
        monthly_income: Gross monthly income.
        existing_emis: Total current monthly EMIs.
        annual_rate: Annual interest rate in percent.
        tenure_months: Tenure in months.
        foir: Fixed Obligation to Income Ratio permitted for EMIs (default 0.5).

    Returns:
        Eligible principal amount (rounded to 2 decimals). Returns 0.0 if the
        available EMI capacity is non-positive.
    """
    available = monthly_income * foir - existing_emis
    if available <= 0:
        return 0.0
    r = _monthly_rate(annual_rate)
    if r == 0:
        return round(available * tenure_months, 2)
    f = (1 + r) ** tenure_months
    return round(available * (f - 1) / (r * f), 2)


def format_inr(amount: float) -> str:
    """Format a number into an INR currency string using Indian digit grouping.

    Args:
        amount: Amount to format.

    Returns:
        String formatted with rupee symbol, Indian grouping commas, and 2 decimals.

    Example:
        >>> format_inr(12345678.9)  # doctest: +SKIP
        '₹1,23,45,678.90'
    """
    neg = amount < 0
    amount = abs(round(amount, 2))
    whole, frac = f"{amount:.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return ("-" if neg else "") + "₹" + whole + "." + frac


def schedule_to_csv(rows: list[dict[str, float]], path: str) -> None:
    """Write an amortisation schedule to a CSV file.

    Args:
        rows: Schedule rows as produced by `amortisation_schedule()`.
        path: Output path to write to.

    Returns:
        None. The file is overwritten if it already exists.
    """
    with open(path, "w") as fh:
        fh.write("month,emi,interest,principal,balance\n")
        for r in rows:
            fh.write(f'{r["month"]},{r["emi"]},{r["interest"]},{r["principal"]},{r["balance"]}\n')


def summary(principal: float, annual_rate: float, tenure_months: int, start: date | None = None) -> dict[str, str]:
    """Build a human-readable summary (primarily for CLI output).

    Args:
        principal: Loan principal amount.
        annual_rate: Annual interest rate in percent.
        tenure_months: Tenure in months.
        start: Optional start date. Defaults to `date.today()`.

    Returns:
        Dict of formatted strings including principal, EMI, totals, and last EMI month.
    """
    start = start or date.today()
    e = emi(principal, annual_rate, tenure_months)
    end_year = start.year + (start.month - 1 + tenure_months) // 12
    end_month = (start.month - 1 + tenure_months) % 12 + 1
    return {
        "principal": format_inr(principal),
        "rate": f"{annual_rate}% p.a.",
        "tenure": f"{tenure_months} months",
        "emi": format_inr(e),
        "total_interest": format_inr(total_interest(principal, annual_rate, tenure_months)),
        "total_payment": format_inr(total_payment(principal, annual_rate, tenure_months)),
        "last_emi": f"{end_year}-{end_month:02d}",
        "currency": DEFAULT_CURRENCY,
    }

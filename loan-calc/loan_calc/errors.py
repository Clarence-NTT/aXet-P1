"""Custom exceptions for loan_calc.

These exceptions are intended to be raised at the public API boundary when
input values are invalid. Internal helpers should generally assume validated
inputs.
"""


class LoanCalcError(Exception):
    """Base class for all loan-calc exceptions."""


class InvalidPrincipalError(LoanCalcError):
    """Raised when principal is non-numeric or <= 0."""


class InvalidRateError(LoanCalcError):
    """Raised when interest rate is non-numeric, negative, or unreasonably high."""


class InvalidTenureError(LoanCalcError):
    """Raised when tenure is non-numeric, non-integer where required, or <= 0."""


class InvalidPrepaymentError(LoanCalcError):
    """Raised when prepayment is invalid (negative amount / month out of range)."""

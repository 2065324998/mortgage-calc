"""Fixed-rate mortgage amortization."""

from .models import Mortgage, PaymentEntry


def calculate_monthly_payment(
    principal: float, annual_rate: float, term_months: int
) -> float:
    """Calculate monthly payment for a fully amortizing loan.

    Uses the standard amortization formula:
        M = P * [r(1+r)^n] / [(1+r)^n - 1]

    where P is principal, r is monthly rate, n is number of payments.
    """
    if annual_rate == 0:
        return round(principal / term_months, 2)
    monthly_rate = annual_rate / 12
    payment = principal * (
        monthly_rate * (1 + monthly_rate) ** term_months
    ) / ((1 + monthly_rate) ** term_months - 1)
    return round(payment, 2)


def generate_fixed_schedule(mortgage: Mortgage) -> list[PaymentEntry]:
    """Generate amortization schedule for a fixed-rate mortgage."""
    payment = calculate_monthly_payment(
        mortgage.loan_amount, mortgage.annual_rate, mortgage.term_months
    )

    balance = mortgage.loan_amount
    entries = []

    for month in range(1, mortgage.term_months + 1):
        monthly_rate = mortgage.annual_rate / 12
        interest = round(balance * monthly_rate, 2)

        if month == mortgage.term_months:
            # Last payment: exact remaining balance + interest
            principal = round(balance, 2)
            payment_amount = round(principal + interest, 2)
        else:
            principal = round(payment - interest, 2)
            payment_amount = payment

        balance = round(balance - principal, 2)

        entries.append(PaymentEntry(
            month=month,
            principal=principal,
            interest=interest,
            balance=max(balance, 0.0),
            rate=mortgage.annual_rate,
            payment=payment_amount,
        ))

    return entries

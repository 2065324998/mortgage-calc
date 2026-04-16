"""High-level mortgage calculator API."""

from .models import Mortgage, MortgageType, AmortizationSchedule
from .fixed import generate_fixed_schedule
from .amortization import generate_arm_schedule
from .escrow import generate_escrow_schedule


def generate_schedule(mortgage: Mortgage) -> AmortizationSchedule:
    """Generate complete amortization schedule with optional escrow.

    Dispatches to the appropriate schedule generator based on mortgage type
    and merges escrow entries if an escrow configuration is provided.
    """
    if mortgage.mortgage_type == MortgageType.FIXED:
        payments = generate_fixed_schedule(mortgage)
    elif mortgage.mortgage_type == MortgageType.ARM:
        payments = generate_arm_schedule(mortgage)
    else:
        raise ValueError(f"Unknown mortgage type: {mortgage.mortgage_type}")

    escrow_entries = []
    if mortgage.escrow is not None:
        escrow_entries = generate_escrow_schedule(
            mortgage.escrow, mortgage.term_months
        )
        for payment, escrow_entry in zip(payments, escrow_entries):
            payment.escrow = escrow_entry.monthly_deposit
            payment.total_payment = round(payment.payment + payment.escrow, 2)
    else:
        for payment in payments:
            payment.total_payment = payment.payment

    return AmortizationSchedule(
        payments=payments,
        escrow_entries=escrow_entries,
    )

"""Mortgage amortization calculator with ARM and escrow support."""

from .models import (
    MortgageType,
    ARMTerms,
    EscrowConfig,
    Mortgage,
    PaymentEntry,
    EscrowEntry,
    AmortizationSchedule,
)
from .fixed import calculate_monthly_payment, generate_fixed_schedule
from .arm import adjust_rate, is_adjustment_month, get_adjustment_number
from .amortization import generate_arm_schedule
from .escrow import calculate_initial_monthly_escrow, generate_escrow_schedule
from .calculator import generate_schedule

__all__ = [
    "MortgageType",
    "ARMTerms",
    "EscrowConfig",
    "Mortgage",
    "PaymentEntry",
    "EscrowEntry",
    "AmortizationSchedule",
    "calculate_monthly_payment",
    "generate_fixed_schedule",
    "adjust_rate",
    "is_adjustment_month",
    "get_adjustment_number",
    "generate_arm_schedule",
    "calculate_initial_monthly_escrow",
    "generate_escrow_schedule",
    "generate_schedule",
]

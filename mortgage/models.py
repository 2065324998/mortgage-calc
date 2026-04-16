"""Data models for mortgage calculations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MortgageType(Enum):
    FIXED = "fixed"
    ARM = "arm"


@dataclass
class ARMTerms:
    """Adjustable-rate mortgage terms.

    Attributes:
        initial_fixed_months: Number of months at the initial fixed rate.
        adjustment_period_months: Months between rate adjustments after fixed period.
        margin: Added to index to get the fully-indexed rate.
        periodic_cap: Maximum rate change per adjustment period.
        lifetime_cap: Maximum total rate increase above initial rate.
        floor_rate: Minimum allowable rate.
        index_rates: Mapping of adjustment number (1-based) to index rate.
        payment_cap: Maximum payment increase per adjustment as a fraction (e.g., 0.075 = 7.5%).
        neg_am_limit: Balance threshold as fraction of original principal (e.g., 1.15 = 115%).
    """
    initial_fixed_months: int
    adjustment_period_months: int
    margin: float
    periodic_cap: float
    lifetime_cap: float
    floor_rate: float
    index_rates: dict[int, float]
    payment_cap: Optional[float] = None
    neg_am_limit: Optional[float] = None
    recast_surcharge: float = 0.025


@dataclass
class EscrowConfig:
    """Escrow account configuration.

    Attributes:
        annual_property_tax: Total annual property tax.
        annual_insurance: Total annual homeowner's insurance premium.
        tax_due_months: Months when property tax is disbursed.
        insurance_due_month: Month when insurance premium is disbursed.
        cushion_months: RESPA-allowed cushion (max 2 months).
        analysis_month: Month of annual escrow analysis.
        tax_increase_rate: Projected annual tax increase rate.
        insurance_increase_rate: Projected annual insurance increase rate.
    """
    annual_property_tax: float
    annual_insurance: float
    tax_due_months: list[int] = field(default_factory=lambda: [4, 10])
    insurance_due_month: int = 12
    cushion_months: int = 2
    analysis_month: int = 3
    tax_increase_rate: float = 0.0
    insurance_increase_rate: float = 0.0


@dataclass
class Mortgage:
    """Complete mortgage definition."""
    loan_amount: float
    annual_rate: float
    term_months: int
    mortgage_type: MortgageType = MortgageType.FIXED
    arm_terms: Optional[ARMTerms] = None
    escrow: Optional[EscrowConfig] = None

    def __post_init__(self):
        if self.mortgage_type == MortgageType.ARM and self.arm_terms is None:
            raise ValueError("ARM mortgage requires arm_terms")


@dataclass
class PaymentEntry:
    """Single month's payment breakdown."""
    month: int
    principal: float
    interest: float
    balance: float
    rate: float
    payment: float
    escrow: float = 0.0
    total_payment: float = 0.0
    is_recast: bool = False
    neg_am_amount: float = 0.0


@dataclass
class EscrowEntry:
    """Escrow account status for a month."""
    month: int
    monthly_deposit: float
    disbursement: float
    balance: float
    shortage_adjustment: float = 0.0


@dataclass
class AmortizationSchedule:
    """Complete amortization schedule."""
    payments: list[PaymentEntry]
    escrow_entries: list[EscrowEntry] = field(default_factory=list)

    @property
    def total_interest(self) -> float:
        return sum(p.interest for p in self.payments)

    @property
    def total_payments(self) -> float:
        return sum(p.payment for p in self.payments)

    @property
    def final_balance(self) -> float:
        return self.payments[-1].balance if self.payments else 0.0

    def payment_at(self, month: int) -> Optional[PaymentEntry]:
        for p in self.payments:
            if p.month == month:
                return p
        return None

    def max_balance(self) -> float:
        return max(p.balance for p in self.payments) if self.payments else 0.0

    def recast_months(self) -> list[int]:
        return [p.month for p in self.payments if p.is_recast]

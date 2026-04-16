"""ARM (Adjustable-Rate Mortgage) rate adjustment logic."""

from .models import ARMTerms


def adjust_rate(
    current_rate: float,
    initial_rate: float,
    new_index: float,
    arm_terms: ARMTerms,
) -> float:
    """Apply rate adjustment with periodic and lifetime caps.

    The periodic cap limits how much the rate can change in a single
    adjustment period. The lifetime cap limits total change from the
    initial rate.

    Args:
        current_rate: The rate currently in effect.
        initial_rate: The original rate at loan origination.
        new_index: The new index value for this adjustment.
        arm_terms: ARM configuration with caps and margin.

    Returns:
        The adjusted rate after applying all caps.
    """
    proposed = new_index + arm_terms.margin

    # Apply periodic cap — limits change per adjustment period
    max_rate = initial_rate + arm_terms.periodic_cap
    min_rate = max(initial_rate - arm_terms.periodic_cap, arm_terms.floor_rate)

    adjusted = max(min_rate, min(max_rate, proposed))

    # Apply lifetime cap — always relative to initial rate
    lifetime_max = initial_rate + arm_terms.lifetime_cap
    adjusted = min(adjusted, lifetime_max)
    adjusted = max(adjusted, arm_terms.floor_rate)

    return round(adjusted, 6)


def is_adjustment_month(month: int, arm_terms: ARMTerms) -> bool:
    """Check if the given month is a rate adjustment month.

    For a 5/1 ARM with initial_fixed_months=60 and adjustment_period_months=12:
    - Months 1-60: fixed period, no adjustments
    - Month 61: first adjustment
    - Month 73: second adjustment
    - Month 85: third adjustment, etc.
    """
    if month <= arm_terms.initial_fixed_months:
        return False
    offset = month - arm_terms.initial_fixed_months - 1
    return offset % arm_terms.adjustment_period_months == 0


def get_adjustment_number(month: int, arm_terms: ARMTerms) -> int:
    """Get which adjustment this is (1-based), or 0 if not an adjustment month."""
    if not is_adjustment_month(month, arm_terms):
        return 0
    offset = month - arm_terms.initial_fixed_months - 1
    return offset // arm_terms.adjustment_period_months + 1

"""ARM amortization schedule generation."""

from .models import Mortgage, PaymentEntry
from .fixed import calculate_monthly_payment
from .arm import adjust_rate, is_adjustment_month, get_adjustment_number


def generate_arm_schedule(mortgage: Mortgage) -> list[PaymentEntry]:
    """Generate amortization schedule for an adjustable-rate mortgage.

    Handles rate adjustments, payment caps, negative amortization,
    and recast events when the balance exceeds the neg-am limit.
    """
    arm = mortgage.arm_terms
    balance = mortgage.loan_amount
    current_rate = mortgage.annual_rate
    initial_rate = mortgage.annual_rate

    payment = calculate_monthly_payment(
        balance, current_rate, mortgage.term_months
    )

    entries = []
    recast_active = False

    for month in range(1, mortgage.term_months + 1):
        remaining_months = mortgage.term_months - month + 1
        is_recast = False

        # Check for rate adjustment
        if is_adjustment_month(month, arm):
            adj_num = get_adjustment_number(month, arm)
            if adj_num in arm.index_rates:
                new_index = arm.index_rates[adj_num]
                current_rate = adjust_rate(
                    current_rate, initial_rate, new_index, arm
                )

                # Recalculate payment for new rate
                payment = calculate_monthly_payment(
                    mortgage.loan_amount, current_rate, remaining_months
                )

                # Apply payment cap if applicable and not in recast
                if arm.payment_cap is not None and not recast_active:
                    prev_payment = entries[-1].payment if entries else payment
                    max_payment = round(
                        prev_payment * (1 + arm.payment_cap), 2
                    )
                    payment = min(payment, max_payment)

        # Calculate interest and principal
        monthly_rate = current_rate / 12
        interest = round(balance * monthly_rate, 2)
        principal = round(payment - interest, 2)

        neg_am = 0.0
        if principal < 0:
            neg_am = abs(principal)
            balance = round(balance + neg_am, 2)
        else:
            balance = round(balance - principal, 2)

        # Final month: pay off remaining balance
        if month == mortgage.term_months and balance > 0:
            principal = round(balance, 2)
            payment = round(principal + interest, 2)
            balance = 0.0

        entries.append(PaymentEntry(
            month=month,
            principal=principal,
            interest=interest,
            balance=max(balance, 0.0),
            rate=current_rate,
            payment=payment,
            is_recast=is_recast,
            neg_am_amount=neg_am,
        ))

    return entries

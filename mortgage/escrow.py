"""Escrow account calculations.

Handles monthly escrow deposits, disbursements for property tax and
insurance, and annual escrow analysis with shortage/surplus adjustments.
"""

from .models import EscrowConfig, EscrowEntry


def calculate_initial_monthly_escrow(escrow: EscrowConfig) -> float:
    """Calculate initial monthly escrow deposit amount."""
    total_annual = escrow.annual_property_tax + escrow.annual_insurance
    return round(total_annual / 12, 2)


def _project_minimum_balance(
    current_balance: float,
    monthly_deposit: float,
    annual_tax: float,
    annual_insurance: float,
    escrow: EscrowConfig,
    start_calendar_month: int,
) -> float:
    """Project the escrow account forward 12 months and find the minimum balance.

    This simulates deposits and disbursements for the next year to
    determine whether the account will have sufficient funds.
    """
    balance = current_balance
    min_balance = balance

    for i in range(12):
        cal_month = ((start_calendar_month - 1 + i) % 12) + 1
        balance += monthly_deposit

        if cal_month in escrow.tax_due_months:
            balance -= annual_tax / len(escrow.tax_due_months)
        if cal_month == escrow.insurance_due_month:
            balance -= annual_insurance

        min_balance = min(min_balance, balance)

    return round(min_balance, 2)


def generate_escrow_schedule(
    escrow: EscrowConfig,
    total_months: int,
    start_month: int = 1,
) -> list[EscrowEntry]:
    """Generate escrow account schedule with annual analysis.

    The escrow account collects monthly deposits and disburses payments
    for property tax and insurance when due. An annual analysis projects
    the next 12 months of activity, finds the minimum projected balance,
    and adjusts the monthly deposit if it would fall below the required
    cushion.

    Per RESPA, any escrow shortage is spread over 12 months.
    """
    monthly_deposit = calculate_initial_monthly_escrow(escrow)
    balance = round(monthly_deposit * escrow.cushion_months, 2)

    current_annual_tax = escrow.annual_property_tax
    current_annual_insurance = escrow.annual_insurance

    entries = []

    for month_offset in range(total_months):
        month = start_month + month_offset
        calendar_month = ((month - 1) % 12) + 1

        shortage_adj = 0.0

        # Annual escrow analysis
        if calendar_month == escrow.analysis_month and month > 12:
            current_annual_tax = round(
                current_annual_tax * (1 + escrow.tax_increase_rate), 2
            )
            current_annual_insurance = round(
                current_annual_insurance * (1 + escrow.insurance_increase_rate), 2
            )

            projected_annual = current_annual_tax + current_annual_insurance
            new_base_monthly = round(projected_annual / 12, 2)

            # Project forward to find minimum balance
            min_projected = _project_minimum_balance(
                balance, new_base_monthly,
                current_annual_tax, current_annual_insurance,
                escrow, calendar_month,
            )

            # Required cushion
            cushion_amount = round(new_base_monthly * escrow.cushion_months, 2)

            if min_projected < cushion_amount:
                shortage = round(cushion_amount - min_projected, 2)
                # Spread shortage over remaining months until next analysis
                remaining_in_year = 12 - calendar_month + 1
                shortage_adj = round(shortage / remaining_in_year, 2)

            monthly_deposit = round(new_base_monthly + shortage_adj, 2)

        # Add monthly deposit
        balance = round(balance + monthly_deposit, 2)

        # Disbursements
        disbursement = 0.0

        if calendar_month in escrow.tax_due_months:
            tax_payment = round(
                current_annual_tax / len(escrow.tax_due_months), 2
            )
            disbursement += tax_payment

        if calendar_month == escrow.insurance_due_month:
            disbursement += round(current_annual_insurance, 2)

        balance = round(balance - disbursement, 2)

        entries.append(EscrowEntry(
            month=month,
            monthly_deposit=monthly_deposit,
            disbursement=disbursement,
            balance=balance,
            shortage_adjustment=shortage_adj,
        ))

    return entries

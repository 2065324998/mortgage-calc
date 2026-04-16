"""Tests for mortgage data models."""

import pytest
from mortgage.models import (
    MortgageType,
    ARMTerms,
    EscrowConfig,
    Mortgage,
    PaymentEntry,
    EscrowEntry,
    AmortizationSchedule,
)


class TestMortgageType:
    def test_fixed_value(self):
        assert MortgageType.FIXED.value == "fixed"

    def test_arm_value(self):
        assert MortgageType.ARM.value == "arm"


class TestARMTerms:
    def test_creation(self):
        arm = ARMTerms(
            initial_fixed_months=60,
            adjustment_period_months=12,
            margin=0.025,
            periodic_cap=0.02,
            lifetime_cap=0.05,
            floor_rate=0.02,
            index_rates={1: 0.04},
        )
        assert arm.initial_fixed_months == 60
        assert arm.margin == 0.025
        assert arm.payment_cap is None
        assert arm.neg_am_limit is None

    def test_optional_fields(self):
        arm = ARMTerms(
            initial_fixed_months=12,
            adjustment_period_months=12,
            margin=0.025,
            periodic_cap=0.02,
            lifetime_cap=0.05,
            floor_rate=0.02,
            index_rates={1: 0.04},
            payment_cap=0.075,
            neg_am_limit=1.15,
        )
        assert arm.payment_cap == 0.075
        assert arm.neg_am_limit == 1.15


class TestEscrowConfig:
    def test_defaults(self):
        escrow = EscrowConfig(
            annual_property_tax=6000.0,
            annual_insurance=1800.0,
        )
        assert escrow.tax_due_months == [4, 10]
        assert escrow.insurance_due_month == 12
        assert escrow.cushion_months == 2
        assert escrow.analysis_month == 3


class TestMortgage:
    def test_fixed_creation(self):
        m = Mortgage(
            loan_amount=300000,
            annual_rate=0.04,
            term_months=360,
        )
        assert m.mortgage_type == MortgageType.FIXED
        assert m.arm_terms is None

    def test_arm_requires_terms(self):
        with pytest.raises(ValueError, match="ARM mortgage requires arm_terms"):
            Mortgage(
                loan_amount=300000,
                annual_rate=0.04,
                term_months=360,
                mortgage_type=MortgageType.ARM,
            )

    def test_arm_with_terms(self):
        arm = ARMTerms(
            initial_fixed_months=60,
            adjustment_period_months=12,
            margin=0.025,
            periodic_cap=0.02,
            lifetime_cap=0.05,
            floor_rate=0.02,
            index_rates={1: 0.04},
        )
        m = Mortgage(
            loan_amount=300000,
            annual_rate=0.04,
            term_months=360,
            mortgage_type=MortgageType.ARM,
            arm_terms=arm,
        )
        assert m.arm_terms is not None


class TestPaymentEntry:
    def test_creation(self):
        entry = PaymentEntry(
            month=1,
            principal=500.0,
            interest=1000.0,
            balance=299500.0,
            rate=0.04,
            payment=1500.0,
        )
        assert entry.month == 1
        assert entry.escrow == 0.0
        assert entry.is_recast is False
        assert entry.neg_am_amount == 0.0


class TestAmortizationSchedule:
    def test_total_interest(self):
        entries = [
            PaymentEntry(1, 500, 1000, 299500, 0.04, 1500),
            PaymentEntry(2, 502, 998, 298998, 0.04, 1500),
        ]
        schedule = AmortizationSchedule(payments=entries)
        assert schedule.total_interest == 1998

    def test_final_balance(self):
        entries = [
            PaymentEntry(1, 500, 1000, 299500, 0.04, 1500),
            PaymentEntry(2, 502, 998, 298998, 0.04, 1500),
        ]
        schedule = AmortizationSchedule(payments=entries)
        assert schedule.final_balance == 298998

    def test_payment_at(self):
        entries = [
            PaymentEntry(1, 500, 1000, 299500, 0.04, 1500),
            PaymentEntry(2, 502, 998, 298998, 0.04, 1500),
        ]
        schedule = AmortizationSchedule(payments=entries)
        assert schedule.payment_at(1).principal == 500
        assert schedule.payment_at(3) is None

    def test_max_balance(self):
        entries = [
            PaymentEntry(1, 500, 1000, 299500, 0.04, 1500),
            PaymentEntry(2, 502, 998, 298998, 0.04, 1500),
        ]
        schedule = AmortizationSchedule(payments=entries)
        assert schedule.max_balance() == 299500

    def test_recast_months_empty(self):
        entries = [
            PaymentEntry(1, 500, 1000, 299500, 0.04, 1500),
        ]
        schedule = AmortizationSchedule(payments=entries)
        assert schedule.recast_months() == []

    def test_empty_schedule(self):
        schedule = AmortizationSchedule(payments=[])
        assert schedule.total_interest == 0
        assert schedule.final_balance == 0.0

"""Tests for the high-level calculator API."""

import pytest
from mortgage.models import (
    MortgageType,
    ARMTerms,
    EscrowConfig,
    Mortgage,
)
from mortgage.calculator import generate_schedule
from mortgage.arm import is_adjustment_month, get_adjustment_number


class TestFixedScheduleViaCalculator:
    def test_generates_schedule(self):
        m = Mortgage(loan_amount=200000, annual_rate=0.05, term_months=360)
        schedule = generate_schedule(m)
        assert len(schedule.payments) == 360

    def test_final_balance(self):
        m = Mortgage(loan_amount=200000, annual_rate=0.05, term_months=360)
        schedule = generate_schedule(m)
        assert schedule.final_balance == pytest.approx(0.0, abs=1.0)


class TestARMAdjustmentTiming:
    """Test the adjustment month detection logic."""

    @pytest.fixture
    def arm_5_1(self):
        return ARMTerms(
            initial_fixed_months=60,
            adjustment_period_months=12,
            margin=0.025,
            periodic_cap=0.02,
            lifetime_cap=0.05,
            floor_rate=0.02,
            index_rates={1: 0.04},
        )

    def test_no_adjustment_during_fixed(self, arm_5_1):
        for month in range(1, 61):
            assert not is_adjustment_month(month, arm_5_1)

    def test_first_adjustment_month(self, arm_5_1):
        assert is_adjustment_month(61, arm_5_1)
        assert get_adjustment_number(61, arm_5_1) == 1

    def test_second_adjustment_month(self, arm_5_1):
        assert is_adjustment_month(73, arm_5_1)
        assert get_adjustment_number(73, arm_5_1) == 2

    def test_non_adjustment_months(self, arm_5_1):
        assert not is_adjustment_month(62, arm_5_1)
        assert not is_adjustment_month(72, arm_5_1)
        assert get_adjustment_number(65, arm_5_1) == 0


class TestARMInitialPeriod:
    """Test ARM schedule during the initial fixed-rate period."""

    def test_initial_payment_matches_fixed(self):
        """During the fixed period, ARM payment should match fixed-rate calc."""
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
        schedule = generate_schedule(m)
        # First payment should use initial rate
        first = schedule.payments[0]
        assert first.rate == 0.04
        assert first.payment == pytest.approx(1432.25, abs=0.01)

    def test_rate_constant_during_fixed(self):
        arm = ARMTerms(
            initial_fixed_months=36,
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
        schedule = generate_schedule(m)
        for i in range(36):
            assert schedule.payments[i].rate == 0.04


class TestEscrowBasic:
    def test_escrow_entries_generated(self):
        escrow = EscrowConfig(
            annual_property_tax=6000.0,
            annual_insurance=1800.0,
        )
        m = Mortgage(
            loan_amount=300000,
            annual_rate=0.04,
            term_months=360,
            escrow=escrow,
        )
        schedule = generate_schedule(m)
        assert len(schedule.escrow_entries) == 360

    def test_initial_monthly_escrow(self):
        escrow = EscrowConfig(
            annual_property_tax=6000.0,
            annual_insurance=1800.0,
        )
        m = Mortgage(
            loan_amount=300000,
            annual_rate=0.04,
            term_months=360,
            escrow=escrow,
        )
        schedule = generate_schedule(m)
        # Initial monthly escrow = (6000 + 1800) / 12 = 650
        assert schedule.escrow_entries[0].monthly_deposit == pytest.approx(650.0, abs=0.01)

    def test_total_payment_includes_escrow(self):
        escrow = EscrowConfig(
            annual_property_tax=6000.0,
            annual_insurance=1800.0,
        )
        m = Mortgage(
            loan_amount=300000,
            annual_rate=0.04,
            term_months=360,
            escrow=escrow,
        )
        schedule = generate_schedule(m)
        first = schedule.payments[0]
        # total_payment = mortgage payment + escrow
        assert first.total_payment == pytest.approx(
            first.payment + 650.0, abs=0.01
        )

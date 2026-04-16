"""Tests for fixed-rate mortgage calculations."""

import pytest
from mortgage.models import Mortgage, MortgageType
from mortgage.fixed import calculate_monthly_payment, generate_fixed_schedule


class TestMonthlyPayment:
    def test_standard_30yr(self):
        """$300,000 at 4% for 30 years."""
        payment = calculate_monthly_payment(300000, 0.04, 360)
        assert payment == pytest.approx(1432.25, abs=0.01)

    def test_15yr(self):
        """$300,000 at 3.5% for 15 years."""
        payment = calculate_monthly_payment(300000, 0.035, 180)
        assert payment == pytest.approx(2144.65, abs=0.01)

    def test_zero_rate(self):
        """Interest-free loan."""
        payment = calculate_monthly_payment(120000, 0.0, 360)
        assert payment == pytest.approx(333.33, abs=0.01)

    def test_small_loan(self):
        """$10,000 at 5% for 5 years."""
        payment = calculate_monthly_payment(10000, 0.05, 60)
        assert payment == pytest.approx(188.71, abs=0.01)


class TestFixedSchedule:
    @pytest.fixture
    def standard_mortgage(self):
        return Mortgage(
            loan_amount=300000,
            annual_rate=0.04,
            term_months=360,
        )

    def test_schedule_length(self, standard_mortgage):
        schedule = generate_fixed_schedule(standard_mortgage)
        assert len(schedule) == 360

    def test_first_payment(self, standard_mortgage):
        schedule = generate_fixed_schedule(standard_mortgage)
        first = schedule[0]
        assert first.month == 1
        assert first.rate == 0.04
        assert first.interest == pytest.approx(1000.0, abs=0.01)
        assert first.principal == pytest.approx(432.25, abs=0.01)

    def test_balance_decreases(self, standard_mortgage):
        schedule = generate_fixed_schedule(standard_mortgage)
        for i in range(1, len(schedule)):
            assert schedule[i].balance <= schedule[i - 1].balance

    def test_final_balance_zero(self, standard_mortgage):
        schedule = generate_fixed_schedule(standard_mortgage)
        assert schedule[-1].balance == pytest.approx(0.0, abs=1.0)

    def test_total_interest(self, standard_mortgage):
        schedule = generate_fixed_schedule(standard_mortgage)
        total_interest = sum(p.interest for p in schedule)
        # Total interest on $300k at 4% for 30 years ≈ $215,609
        assert total_interest == pytest.approx(215609, abs=50)

    def test_consistent_payment(self, standard_mortgage):
        """All payments except last should be identical."""
        schedule = generate_fixed_schedule(standard_mortgage)
        expected = schedule[0].payment
        for entry in schedule[:-1]:
            assert entry.payment == expected

"""Pure-python tests: `python -m pytest mongolia_payroll/tests` (no bench needed)."""

import datetime
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mongolia_payroll.calculator import (
	ACCIDENT,
	PayrollRules,
	average_daily_wage,
	norm_working_days,
)

rules = PayrollRules()  # 792,000₮ доод хэмжээ, дээд хязгаар 7,920,000₮


def test_ndsh_employee_is_11_5_percent():
	assert rules.employee_total_rate == pytest.approx(11.5)
	assert rules.ndsh_employee(2_000_000) == 230_000


def test_ndsh_ceiling_is_ten_times_minimum_wage():
	assert rules.ndsh_ceiling == 7_920_000
	assert rules.ndsh_base(10_000_000) == 7_920_000
	assert rules.ndsh_employee(10_000_000) == pytest.approx(7_920_000 * 0.115)


def test_ndsh_employer_depends_on_risk_class():
	assert rules.ndsh_employer(1_000_000) == 125_000  # I зэрэг, 12.5%
	assert rules.ndsh_employer(1_000_000, accident_rate=2.5) == 145_000  # III зэрэг, 14.5%
	assert rules.employer_rates_for(1.5)[ACCIDENT] == 1.5


def test_pit_progressive_slabs():
	assert rules.pit_before_credit(5_000_000) == 500_000
	# 6 сая x 10% + 4 сая x 15%
	assert rules.pit_before_credit(10_000_000) == 600_000 + 600_000
	# 6 x 10% + 6 x 15% + 3 x 20%
	assert rules.pit_before_credit(15_000_000) == 600_000 + 900_000 + 600_000


def test_pit_credit_slabs():
	assert rules.pit_credit(500_000) == 20_000
	assert rules.pit_credit(800_000) == 18_000
	assert rules.pit_credit(2_600_000) == 10_000
	assert rules.pit_credit(3_000_001) == 0
	assert rules.pit_credit(0) == 0


def test_pit_withholding_after_ndsh_and_credit():
	wage = 1_000_000
	ndsh = rules.ndsh_employee(wage)  # 115,000
	# (1,000,000 - 115,000) x 10% - 18,000
	assert rules.pit(wage, ndsh) == 88_500 - 18_000


def test_pit_never_negative():
	assert rules.pit(100_000, 11_500) == 0


def test_overtime_and_holiday_pay():
	# 22 ажлын өдөр x 8 цаг = 176 цаг, 1,760,000₮ -> 10,000₮/цаг
	assert rules.hourly_rate(1_760_000, 22) == 10_000
	assert rules.overtime_pay(1_760_000, 22, 4) == 60_000
	assert rules.holiday_pay(1_760_000, 22, 8) == 160_000


def test_vacation_pay():
	daily = average_daily_wage(24_000_000, 240)
	assert daily == 100_000
	assert rules.vacation_pay(daily, 15) == 1_500_000
	assert average_daily_wage(1000, 0) == 0


def test_norm_working_days():
	# 2026 оны 10-р сар: 22 ажлын өдөр (Даваа-Баасан)
	assert norm_working_days(datetime.date(2026, 10, 1)) == 22
	weekend_and_holidays = [datetime.date(2026, 10, d) for d in (3, 4, 10, 11, 17, 18, 24, 25, 31)]
	assert norm_working_days(datetime.date(2026, 10, 15), weekend_and_holidays) == 22


def test_excel_layout():
	from io import BytesIO

	from openpyxl import load_workbook

	from mongolia_payroll.excel import build_workbook

	columns = [
		{"fieldname": "last_name", "label": "Овог", "fieldtype": "Data"},
		{"fieldname": "base", "label": "Шимтгэл ногдуулах орлого", "fieldtype": "Currency"},
	]
	rows = [{"last_name": "Бат", "base": 1_000_000}, {"last_name": "Нийт", "base": 1_000_000, "bold": 1}]
	content = build_workbook("НД-8", [("Ажил олгогч", "Тест ХХК")], columns, rows)
	ws = load_workbook(BytesIO(content)).active
	assert ws["A1"].value == "НД-8"
	assert ws["B2"].value == "Тест ХХК"
	assert [c.value for c in ws[4]] == ["Овог", "Шимтгэл ногдуулах орлого"]
	assert ws["B5"].value == 1_000_000
	assert ws["A6"].font.bold

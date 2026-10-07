import frappe

from erpnext.regional.mongolia.setup import setup


def execute():
	companies = frappe.get_all("Company", filters={"country": "Mongolia"}, pluck="name")
	if not companies:
		return

	frappe.reload_doc("regional", "doctype", "e_barimt_settings")
	for company in companies:
		setup(company)

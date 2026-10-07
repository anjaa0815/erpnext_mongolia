# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import getdate, nowdate

# Withholding taxes a Mongolian company deducts from payments to suppliers.
# (category name, rate, account number in the Mongolian chart, account name)
WITHHOLDING_CATEGORIES = [
	("ХХОАТ 10% - Ажил, үйлчилгээ", 10, "3302", "ХХОАТ-ын өглөг"),
	("ХХОАТ 10% - Хөрөнгийн түрээс", 10, "3302", "ХХОАТ-ын өглөг"),
	("ХХОАТ 10% - Эрхийн шимтгэл (роялти)", 10, "3302", "ХХОАТ-ын өглөг"),
	("ААНОАТ 20% - Оршин суугч бус этгээд", 20, "3303", "ААНОАТ-ын өглөг"),
]


def setup(company=None, patch=True):
	make_custom_fields()
	if company:
		setup_tax_withholding_categories(company)


def make_custom_fields(update=True):
	invoice_fields = [
		dict(
			fieldname="ebarimt_section",
			label="E-Barimt",
			fieldtype="Section Break",
			insert_after="po_date",
			collapsible=1,
		),
		dict(
			fieldname="ebarimt_type",
			label="E-Barimt Type",
			fieldtype="Select",
			options="\nB2C_RECEIPT\nB2B_RECEIPT\nB2C_INVOICE\nB2B_INVOICE",
			description="Leave empty to choose automatically from the customer and payment.",
			insert_after="ebarimt_section",
			print_hide=1,
		),
		dict(
			fieldname="ebarimt_consumer_no",
			label="Consumer E-Barimt No",
			fieldtype="Data",
			description="8-digit E-Barimt number of an individual customer.",
			insert_after="ebarimt_type",
			print_hide=1,
		),
		dict(
			fieldname="ebarimt_customer_tin",
			label="Customer TIN",
			fieldtype="Data",
			description="Filled from the customer's registration number when left empty.",
			insert_after="ebarimt_consumer_no",
			print_hide=1,
		),
		dict(fieldname="ebarimt_column_break", fieldtype="Column Break", insert_after="ebarimt_customer_tin"),
		dict(
			fieldname="ebarimt_status",
			label="E-Barimt Status",
			fieldtype="Select",
			options="\nSent\nFailed\nCancelled\nReturn Processed",
			insert_after="ebarimt_column_break",
			read_only=1,
			no_copy=1,
			allow_on_submit=1,
			in_standard_filter=1,
			print_hide=1,
		),
		dict(
			fieldname="ebarimt_id",
			label="E-Barimt Receipt ID",
			fieldtype="Data",
			insert_after="ebarimt_status",
			read_only=1,
			no_copy=1,
			allow_on_submit=1,
			in_standard_filter=1,
		),
		dict(
			fieldname="ebarimt_lottery",
			label="E-Barimt Lottery No",
			fieldtype="Data",
			insert_after="ebarimt_id",
			read_only=1,
			no_copy=1,
			allow_on_submit=1,
		),
		dict(
			fieldname="ebarimt_date",
			label="E-Barimt Date",
			fieldtype="Datetime",
			insert_after="ebarimt_lottery",
			read_only=1,
			no_copy=1,
			allow_on_submit=1,
			print_hide=1,
		),
		dict(
			fieldname="ebarimt_previous_id",
			label="Replaced E-Barimt Receipt ID",
			fieldtype="Data",
			insert_after="ebarimt_date",
			read_only=1,
			no_copy=1,
			allow_on_submit=1,
			print_hide=1,
		),
		dict(
			fieldname="ebarimt_qr_data",
			label="E-Barimt QR Data",
			fieldtype="Small Text",
			insert_after="ebarimt_previous_id",
			read_only=1,
			no_copy=1,
			allow_on_submit=1,
			hidden=1,
			print_hide=1,
		),
		dict(
			fieldname="ebarimt_error",
			label="E-Barimt Error",
			fieldtype="Small Text",
			insert_after="ebarimt_qr_data",
			read_only=1,
			no_copy=1,
			allow_on_submit=1,
			depends_on="eval:doc.ebarimt_status=='Failed'",
			print_hide=1,
		),
	]

	custom_fields = {
		"Sales Invoice": invoice_fields,
		"POS Invoice": invoice_fields,
		"Item": [
			dict(
				fieldname="ebarimt_classification_code",
				label="E-Barimt Classification Code",
				fieldtype="Data",
				description="Product and service classification code (БҮНА) reported on E-Barimt receipts.",
				insert_after="item_group",
			),
			dict(
				fieldname="ebarimt_tax_type",
				label="E-Barimt Tax Type",
				fieldtype="Select",
				options="\nVAT_ABLE\nVAT_FREE\nVAT_ZERO\nNO_VAT",
				description="Used when no VAT is charged on the item. VAT_FREE and VAT_ZERO need a Tax Product Code.",
				insert_after="ebarimt_classification_code",
			),
			dict(
				fieldname="ebarimt_tax_product_code",
				label="E-Barimt Tax Product Code",
				fieldtype="Data",
				depends_on="eval:['VAT_FREE','VAT_ZERO'].includes(doc.ebarimt_tax_type)",
				insert_after="ebarimt_tax_type",
			),
		],
		"Customer": [
			dict(
				fieldname="ebarimt_tin",
				label="TIN",
				fieldtype="Data",
				description="Taxpayer identification number, looked up from the Tax ID (registration number).",
				insert_after="tax_id",
			),
			dict(
				fieldname="ebarimt_vat_payer",
				label="VAT Payer",
				fieldtype="Check",
				read_only=1,
				insert_after="ebarimt_tin",
			),
		],
	}

	create_custom_fields(custom_fields, update=update)


def setup_tax_withholding_categories(company):
	year_start = getdate(nowdate()).replace(month=1, day=1)

	for category_name, rate, account_number, account_name in WITHHOLDING_CATEGORIES:
		account = get_withholding_account(company, account_number, account_name)
		if not account:
			continue

		if frappe.db.exists("Tax Withholding Category", category_name):
			doc = frappe.get_doc("Tax Withholding Category", category_name)
			if any(row.company == company for row in doc.accounts):
				continue
			doc.append("accounts", {"company": company, "account": account})
			doc.save(ignore_permissions=True)
			continue

		frappe.get_doc(
			{
				"doctype": "Tax Withholding Category",
				"name": category_name,
				"category_name": category_name,
				"tax_deduction_basis": "Net Total",
				"rates": [
					{
						"tax_withholding_rate": rate,
						"from_date": year_start,
						"to_date": year_start.replace(year=2099, month=12, day=31),
					}
				],
				"accounts": [{"company": company, "account": account}],
			}
		).insert(ignore_permissions=True)


def get_withholding_account(company, account_number, account_name):
	account = frappe.db.get_value(
		"Account", {"company": company, "account_number": account_number, "is_group": 0}
	) or frappe.db.get_value("Account", {"company": company, "account_name": account_name, "is_group": 0})
	if account:
		return account

	from erpnext.setup.setup_wizard.operations.taxes_setup import get_or_create_account

	try:
		return get_or_create_account(company, {"account_name": account_name}).name
	except Exception:
		frappe.log_error(_("Could not create withholding tax account {0}").format(account_name))
		return None

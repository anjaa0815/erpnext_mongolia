app_name = "mongolia_payroll"
app_title = "Mongolia Payroll"
app_publisher = "Anjaa"
app_description = "Mongolian payroll localization for Frappe HRMS (НДШ, ХХОАТ, НД-7, НД-8)"
app_email = "anjaaariunjargal@gmail.com"
app_license = "gpl-3.0"

required_apps = ["erpnext", "hrms"]

after_install = "mongolia_payroll.install.after_install"
after_migrate = "mongolia_payroll.install.after_migrate"

# Make the mn_* helpers callable from Salary Component formulas.
before_request = ["mongolia_payroll.formula.register"]
before_job = ["mongolia_payroll.formula.register"]

doc_events = {
	"Salary Slip": {"before_validate": "mongolia_payroll.formula.register_on_doc"},
	"Salary Structure Assignment": {"before_validate": "mongolia_payroll.formula.register_on_doc"},
}

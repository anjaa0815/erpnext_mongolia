// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

["Sales Invoice", "POS Invoice"].forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		refresh(frm) {
			if (frm.doc.docstatus !== 1 || !frm.fields_dict.ebarimt_status) return;

			if (frm.doc.ebarimt_status === "Failed") {
				frm.dashboard.set_headline_alert(
					__("E-Barimt receipt was not registered: {0}", [
						frappe.utils.escape_html(frm.doc.ebarimt_error || ""),
					]),
					"orange"
				);
				frm.add_custom_button(
					__("Resend to E-Barimt"),
					() =>
						frappe
							.call({
								method: "erpnext.regional.mongolia.ebarimt.resend",
								args: { doctype: frm.doctype, name: frm.docname },
								freeze: true,
							})
							.then(() => frm.reload_doc()),
					__("Actions")
				);
			}
		},
	});
});

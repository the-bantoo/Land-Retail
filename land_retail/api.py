import frappe
from frappe import _


@frappe.whitelist()
def notification_email(payment_entry, method):
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                if ((invoice.total - invoice.outstanding_amount) >= (invoice.total * 0.2)) & ((invoice.total - invoice.outstanding_amount) < (invoice.total * 0.5)):
                    frappe.sendmail(
                        recipients="duncan@thebantoo.com",
                        sender="erp@thebantoo.com",
                        subject="20" + "%" + " Plot Payment",
                        message="Plot Payment Email Test"
                    )
                    invoice.payment_notification = 'Partly Paid'
                    invoice.save()
                    frappe.msgprint(_("Hello World!"))
                elif ((invoice.total - invoice.outstanding_amount) >= (invoice.total * 0.5)) & ((invoice.total - invoice.outstanding_amount) < invoice.total):
                    frappe.sendmail(
                        recipients="duncan@thebantoo.com",
                        sender="erp@thebantoo.com",
                        subject="50" + "%" + " Plot Payment",
                        message="Plot Payment Email Test"
                    )
                    invoice.payment_notification = 'Paid In Half'
                    frappe.msgprint(_("Hello Space!"))
                elif (invoice.outstanding_amount == 0):
                    frappe.sendmail(
                        recipients="duncan@thebantoo.com",
                        sender="erp@thebantoo.com",
                        subject="100" + "%" + " Plot Payment",
                        message="Plot Payment Email Test"
                    )
                    invoice.payment_notification = 'Paid In Full'
                    frappe.msgprint(_("Hello Universe!"))

def add_plots_to_payment_entry(payment_entry, method):
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                for item in invoice.items:
                    if item.item_code:
                        ref.plot = item.item_code

def create_item(plot, method):
    settings = frappe.get_doc('Land Settings')
    plot_item = frappe.get_doc({
        "doctype": "Item",
        "item_group": settings.land_for_sale_group,
        "default_warehouse": settings.sales_land_warehouse,
        "item_code": "Plot " + str(plot.plot_id),
        "land": 1,
        "is_stock_item": 1,
        "stock_uom": "Square Meter",
        "opening_stock": plot.area,
        "standard_rate": plot.plot_price,
        "is_purchase_item": 0,
        "is_sales_item": 1,
        "include_item_in_manufacturing": 0,
        "description": "Project: " + str(plot.project) + "<br>" + "Subdivision: " + str(plot.subdivision) + "<br>" + "Plot ID: " + str(plot.plot_id) + "<br>" + "Dimensions: " + str(plot.dimensions) + "<br>" + "Area: " + str(plot.area) + "sqm",
    })
    plot_item.flags.ignore_permission = True
    plot.plot_id = "Plot " + plot.plot_id
    plot.plot_no = plot.plot_id
    plot_item.insert()
    plot.save()

def calculate_plot_details(plot, method):
    if not plot.area or int(plot.area) <= 0:
        plot.area = int(plot.width) * int(plot.length)

    plot.dimensions = str(plot.width) + " x " + str(plot.length) + "m"

def project_item(project, method):
    settings = frappe.get_doc('Land Settings')
    project_item = frappe.get_doc({
        "doctype": "Item",
        "item_name": project.project_name,
        "item_group": settings.land_in_bulk_group,
        "land": 1,
        "item_code": project.project_name,
        "is_stock_item": 1,
        "stock_uom": "Square Meter",
        "include_item_in_manufacturing": 0,
    })
    project_item.flags.ignore_permission = True
    project_item.insert()

def count_invoiced_plots(invoice, method):
    count = 1
    for item in invoice.items:
        if item.plot_id:
            if count > 1:
                frappe.throw("Only one plot is allowed per invoice")
            count += 1

def add_outstanding_amount_to_plot(payment_entry, method):
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                for item in invoice.items:
                    doc = frappe.get_doc("Plot", ref.plot)
                    if item.item_code != ref.plot:
                        continue
                    doc.outstanding_balance = invoice.outstanding_amount
                    doc.customer = invoice.customer_name
                    doc.sales_invoice = ref.reference_name
                    doc.paid_amount = invoice.total - invoice.outstanding_amount
                    doc.save()

def reservation_fee(land_settings, method):
    plot = frappe.get_doc("Plot")
    plot.reservation_fee = land_settings.reservation_fee
    plot.save()

def cancel_payment(payment_entry, method):
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                sales_invoice = frappe.get_doc(
                    "Sales Invoice", ref.reference_name)
                for item in sales_invoice.items:
                    doc = frappe.get_doc('Plot', ref.plot)
                    if item.item_code != ref.plot:
                        continue
                    doc.balance = int(doc.outstanding_balance) + \
                        payment_entry.total_allocated_amount
                    doc.customer_name = sales_invoice.customer_name
                    doc.sales_invoice = ref.reference_name
                    doc.value = int(doc.paid_amount) - \
                        payment_entry.total_allocated_amount
                    doc.save()
                    if doc.paid_amount == 0:
                        doc.customer = ""
                        doc.sales_invoice = ""
                        doc.outstanding_balance = 0
                        doc.save()

def plot_project(sales_invoice, method):
    count = 1
    for item in sales_invoice.items:
        if count > 1:
            for item in sales_invoice.items:
                settings = frappe.get_doc('Land Settings')
                if item.item_name == settings.construction_item:
                    continue
                doc = frappe.get_doc('Plot', item.item_name)
                project = frappe.get_doc({
                    "doctype": "Project",
                    "project_name": "Construction on " + str(doc.plot_id),
                    "status": "Open",
                })
                project.flags.ignore_permission = True
                project.save()
        count += 1

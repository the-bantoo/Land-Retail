import frappe
from frappe import _

#Plot
def create_item(plot, method):
    settings = frappe.get_doc('Land Settings')
    plot_item = frappe.get_doc({
        "doctype": "Item",
        "item_group": settings.land_for_sale_group,
        "default_warehouse": settings.sales_land_warehouse,
        "item_code": plot.plot_id,
        "land": 1,
        "is_stock_item": 1,
        "stock_uom": "Square Meter",
        "standard_rate": plot.plot_price / plot.area,
        "is_purchase_item": 0,
        "is_sales_item": 1,
        "include_item_in_manufacturing": 0,
        "description": "Project: " + str(plot.project) + "<br>" + "Subdivision: " + str(plot.subdivision) + "<br>" + "Plot ID: " + str(plot.plot_id) + "<br>" + "Dimensions: " + str(plot.dimensions) + "<br>" + "Area: " + str(plot.area) + "sqm",
    })
    plot_item.flags.ignore_permission = True
    plot_item.insert()
    plot.reservation_fee = settings.reservation_fee
    plot.plot_no = plot.plot_id
    plot.save()

def calculate_area(plot, method):
    if not plot.area or int(plot.area) <= 0:
        plot.area = int(plot.width) * int(plot.length)

    plot.dimensions = str(plot.width) + " x " + str(plot.length) + "m"

#Payment Entry
def payment_update(payment_entry, method):
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                for item in invoice.items:
                    settings = frappe.get_doc('Land Settings')
                    if item.item_name == settings.construction_item:
                        continue
                    doc = frappe.get_doc("Plot", item.item_name)
                    doc.outstanding_balance = invoice.outstanding_amount
                    doc.customer_name = invoice.customer_name
                    doc.sales_invoice = ref.reference_name
                    doc.paid_amount = payment_entry.total_allocated_amount
                    doc.save()

def cancel_payment(payment_entry, method):
    settings = frappe.get_doc("Land Settings")
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                sales_invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                for item in sales_invoice.items:
                    if item.item_name == settings.construction_item:
                        continue
                    doc = frappe.get_doc('Plot', item.item_name)
                    doc.outstanding_balance = int(doc.outstanding_balance) + payment_entry.total_allocated_amount
                    doc.customer_name = sales_invoice.customer_name
                    doc.sales_invoice = ref.reference_name
                    doc.paid_amount = int(doc.paid_amount) - payment_entry.total_allocated_amount
                    doc.save()
                    if doc.paid_amount == 0:
                        doc.customer_name = ""
                        doc.sales_invoice = ""
                        doc.outstanding_balance = 0
                        doc.save()
                        
def add_plot(payment_entry, method):
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                for item in invoice.items:
                    if item.plot_id:
                        ref.plot = item.item_code         

#Sales Invoice
def plot_details(invoice, method):
    settings = frappe.get_doc("Land Settings")
    for item in invoice.items:
        if item.item_code == settings.construction_item:
            continue
        plot = frappe.get_doc("Plot", item.item_code)
        item.plot_id = plot.plot_id
        item.plot_project = plot.project
        item.plot_subdivision = plot.subdivision
      
def count_invoiced_plots(invoice, method):
    count = 1
    for item in invoice.items:
        if item.plot_id:
            if count > 1:
                frappe.throw("Only one plot is allowed per invoice")
            count += 1


def plot_project(payment_entry, method):
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                for item in invoice.items:
                    settings = frappe.get_doc('Land Settings')
                    if item.item_name == settings.construction_item and payment_entry.total_allocated_amount == 0.5 * invoice.total:
                        continue
                    plot = frappe.get_doc("Plot", item.item_name)
                    plot_project = frappe.get_doc({
                        "doctype": "Project",
                        "project_name": "Plot " + str(plot.plot_id),
                        "status": "Open",

                    })
                    plot_project.flags.ignore_permission = True
                    plot_project.insert()

import frappe
import json
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
        "standard_rate": plot.plot_price / plot.area,
        "is_purchase_item": 0,
        "is_sales_item": 1,
        "include_item_in_manufacturing": 0,
        "description": "Project: " + str(plot.project) + "<br>" + "Subdivision: " + str(plot.subdivision) + "<br>" + "Plot ID: " + str(plot.plot_id) + "<br>" + "Dimensions: " + str(plot.dimensions) + "<br>" + "Area: " + str(plot.area) + "sqm",
    })
    plot_item.flags.ignore_permission = True
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
                    settings = frappe.get_doc('Land Settings')
                    if item.item_name == settings.construction_item:
                        continue
                    doc = frappe.get_doc("Plot", item.item_name)
                    doc.balance = invoice.outstanding_amount
                    doc.customer_name = invoice.customer_name
                    doc.customer_sales_invoice = ref.reference_name
                    doc.value = invoice.total - invoice.outstanding_amount
                    doc.save()


def reservation_fee(land_settings, method):
    plot = frappe.get_doc("Plot")
    plot.reservation_fee = land_settings.reservation_fee
    plot.save()


def cancel_payment(payment_entry, method):
    settings = frappe.get_doc('Land Settings')
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                sales_invoice = frappe.get_doc(
                    "Sales Invoice", ref.reference_name)
                for item in sales_invoice.items:
                    if item.item_name == settings.construction_item:
                        continue
                    doc = frappe.get_doc("Plot", item.item_name)
                    doc.balance = int(doc.balance) + \
                        payment_entry.total_allocated_amount
                    doc.customer_name = sales_invoice.customer_name
                    doc.customer_sales_invoice = ref.reference_name
                    doc.value = int(doc.value) - \
                        payment_entry.total_allocated_amount
                    doc.save()
                    if doc.value == 0:
                        doc.customer_name = ""
                        doc.customer_sales_invoice = ""
                        doc.balance = 0
                        doc.save()


def plot_project(sales_invoice, method):
    count = 1
    for item in sales_invoice.items:
        if count > 1:
            for item in sales_invoice.items:
                settings = frappe.get_doc('Land Settings')
                if item.item_name == settings.construction_item:
                    continue
                if sales_invoice.outstanding_amount <= (0.5 * sales_invoice.total):
                    doc = frappe.get_doc('Plot', item.item_name)
                    project = frappe.get_doc({
                        "doctype": "Project",
                        "project_name": "Construction on " + str(doc.plot_id),
                        "status": "Open",
                    })
                    project.flags.ignore_permission = True
                    project.save()
                    doc.plot_project = "Construction on " + str(doc.plot_id)
                    doc.save()
        count += 1
        
@frappe.whitelist()
def get_new_plots(name = None):
    sub = frappe.get_doc('Subdivision', name)
    sub_plots = sub.plots
    num_sub_plots = len(sub_plots)
    all_plots = frappe.get_all('Plot', filters={'subdivision': name}, fields=['name', 'customer_name', 'status'])#Get all plots
    num_all_plots = len(all_plots)
    count = 0
    
    if int(num_all_plots) > int(num_sub_plots):
        for plot in all_plots:
            if not any(sub_plot.plot_id == plot['name'] for sub_plot in sub_plots):
                sub.append("plots", plot)
                count += 1
                
        if count > 0:
            sub.save()

@frappe.whitelist()
def get_new_subdivisions(name = None):
    project = frappe.get_doc('Project', name)
    project_subs = project.subdivision
    num_project_subs = len(project_subs)
    all_subs = frappe.get_all('Subdivision', filters={'project': name}, fields=['name'])#Get all subdivisions
    frappe.msgprint(str(all_subs))
    num_all_subs = len(all_subs)
    count = 0

    if int(num_all_subs) > int(num_project_subs):
        for subdivision in all_subs:
            if not any(project_subs.subdivision == subdivision['name'] for project_subs in project_subs):
                project.append("subdivision", subdivision)
                frappe.msgprint(str(project))
                count += 1
        
        if count > 0:
            project.save()
            frappe.msgprint("Done!")
            
@frappe.whitelist()
def plot_coordinates(name):
    coordinates = frappe.get_all('Coordinates', filters={'plots': name}, fields=['latitude', 'longitude'])
    
    plot = frappe.get_all('Plot', filters={'plot_id': name}, fields=['plot_id', 'plot_no', 'subdivision', 'project', 'area', 'length', 'width', 
    'status', 'plot_price', 'map', 'customer_name', 'plot_project', 'value', 'balance', 'reservation_fee', 'dimensions'])
    plot_info = plot + coordinates

@frappe.whitelist()
def sub_coordinates(name):
    subdivision = frappe.get_doc('Subdivision', name)
    plots = subdivision.plots
    subdivision_plot_info = []
    for plot in plots:
        plot_index = frappe.get_doc('Plot', plot.plot_id)
        subdivision_plot_info.append(plot_index)
    #for plot in subdivision.plots:
    #    coordinates = frappe.get_all('Coordinates', filters={'plots': plot}, fields=['latitude', 'longitude', 'plots'])
    #    frappe.msgprint(coordinates)
    #frappe.msgprint(subdivision.title)
    #return subdivision.title
    #return frappe.db.count('Subdivision')
    #subdivisions = frappe.get_doc(doctype, name)
    
    return subdivision_plot_info
 
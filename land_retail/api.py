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
    plot.outstanding_balance = plot.plot_price
    plot.status = settings.default_status
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
                    plot = frappe.get_doc("Plot", item.item_name)
                    plot.outstanding_balance = invoice.outstanding_amount
                    plot.customer_name = invoice.customer_name
                    plot.sales_invoice = ref.reference_name
                    plot.paid_amount = payment_entry.total_allocated_amount
                    plot.save()
                    if plot.paid_amount > plot.reservation_fee and plot.paid_amount < plot.plot_price:
                        plot.status = "Partially Paid"
                        plot.save()
                    elif plot.paid_amount > 0 and plot.paid_amount <= plot.reservation_fee:
                        plot.status = "Reserved"
                        plot.save()
                    elif plot.paid_amount >= plot.plot_price and plot.outstanding_balance == 0:
                        plot.status = "Sold"
                        plot.save()
                    

def cancel_payment(payment_entry, method):
    settings = frappe.get_doc("Land Settings")
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                sales_invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                for item in sales_invoice.items:
                    if item.item_name == settings.construction_item:
                        continue
                    plot = frappe.get_doc('Plot', item.item_name)
                    plot.outstanding_balance = int(plot.outstanding_balance) + payment_entry.total_allocated_amount
                    plot.customer_name = sales_invoice.customer_name
                    plot.sales_invoice = ref.reference_name
                    plot.paid_amount = int(plot.paid_amount) - payment_entry.total_allocated_amount
                    plot.save()
                    if plot.paid_amount == 0:
                        plot.customer_name = ""
                        plot.sales_invoice = ""
                        plot.outstanding_balance = 0
                        plot.status = "Available"
                        plot.save()
                        
                        
def add_plot(payment_entry, method):
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                for item in invoice.items:
                    if item.plot_id:
                        ref.plot = item.item_code         

def plot_project(payment_entry, method):
    if payment_entry.payment_type == "Receive":
        for ref in payment_entry.references:
            if(ref.reference_doctype == "Sales Invoice"):
                invoice = frappe.get_doc("Sales Invoice", ref.reference_name)
                for item in invoice.items:
                    settings = frappe.get_doc('Land Settings')
                    if item.item_name == settings.construction_item:
                        continue
                    plotproject = "Plot " + str(item.plot_id)
                    project = frappe.get_list("Project", fields=['project_name'])
                    if plotproject in project:
                        frappe.errprint("Present!")
                    else:
                        frappe.errprint("Not present!")
                        

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

                        
#Map Coordinates
@frappe.whitelist()
def sub_coordinates(name):
    subdivision = frappe.get_doc('Subdivision', name)
    plots = subdivision.plots
    subdivision_plot_info = []
    for plot in plots:
        plot_index = frappe.get_doc('Plot', plot.plot_id)
        subdivision_plot_info.append(plot_index)
    
    return subdivision_plot_info

@frappe.whitelist()
def return_subdivisions(project_name):
    all_subdivisions = frappe.get_all('Subdivision', filters={'project': project_name}, fields=['title'])
    
    project_subdivisions = []
    for all_subdivision_details in all_subdivisions:
        subdiv =  frappe.get_doc('Subdivision', all_subdivision_details.title)
        project_subdivisions.append(subdiv);
    return project_subdivisions
    
@frappe.whitelist()
def return_subdivision_plots(subdivision_name):
    all_subdivision_plots = frappe.get_all('Plot', filters={'subdivision': subdivision_name}, fields=['plot_id'])
    
    subdivision_plots = []
    for subdivision_plot in all_subdivision_plots:
        subdiv_plot = frappe.get_doc('Plot', subdivision_plot.plot_id)
        subdivision_plots.append(subdiv_plot)
    return subdivision_plots

#Project
def project_item(project, method):
    settings = frappe.get_doc('Land Settings')
    if project.project_type == "Land":
        item = frappe.get_doc({
            "doctype": "Item",
            "item_group": settings.land_in_bulk_group,
            "default_warehouse": settings.bulk_land_warehouse,
            "item_code": project.project_name,
            "land": 1,
            "is_stock_item": 1,
            "stock_uom": "Square Meter",
            "is_purchase_item": 1,
            "is_sales_item": 1,
            "include_item_in_manufacturing": 0,
            "description": "Project Name: " + str(project.project_name) + "<br>" + "Project Area: " + str(project.area_sqm) + "sqm",
            
        })
        item.flags.ignore_permission = True
        item.insert()

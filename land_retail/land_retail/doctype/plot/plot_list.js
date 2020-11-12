frappe.listview_settings['Plot'] = {
    add_fields: ["status", "paid_amount", "outstanding_amount", "plot_price"],
    
    get_indicator: function (plot) {
        if (plot.paid_amount <= 1000) {
            return [__("Reserved"), "orange"];
        } else if (plot.paid_amount > 1000 && plot.paid_amount < plot.plot_price) {
            return [__("Paid"), "blue"];
        } else if (plot.paid_amount == plot.plot_price) {
            return [__("Completed"), "darkgrey"];
        } else {
            return [__("Available"), "green"];
        }
    }
};

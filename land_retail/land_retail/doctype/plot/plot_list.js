frappe.listview_settings['Plot'] = {
    add_fields: ["status", "paid_amount", "outstanding_amount", "plot_price", "reservation_fee"],

    get_indicator: function (plot, land_settings) {
        if (plot.paid_amount <= plot.reservation_fee && plot.paid_amount > 0) {
            return [__("Reserved"), "orange"];
        } else if (plot.paid_amount > plot.reservation_fee && plot.paid_amount < plot.plot_price) {
            return [__("Paid"), "blue"];
        } else if (plot.paid_amount == plot.plot_price) {
            return [__("Completed"), "darkgrey"];
        } else {
            return [__("Available"), "green"];
        }
    }
};

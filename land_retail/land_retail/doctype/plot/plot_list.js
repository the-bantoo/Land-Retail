frappe.listview_settings['Plot'] = {
	add_fields: ["status", "paid_amount", "outstanding_amount", "plot_price", "reservation_fee"],
	get_indicator: function(plot) {
		var status_color = {
			"Partially Paid": "blue",
			"Reserved": "orange",
			"Available": "green",
			"Sold": "red",
		};
		return [__(plot.status), status_color[plot.status], "status,=,"+plot.status];
	},
};

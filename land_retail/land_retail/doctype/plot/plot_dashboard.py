"""
from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'heatmap': True,
		'heatmap_message': _('This is based on transactions against this Plot. See timeline below for details'),
	
		'transactions': [
			{
				'label': _('Orders'),
				'items': ['Customer', 'Sales Invoice']
			},
			{
				'label': _('Payments'),
				'items': ['Payment Entry', 'Bank Account']
			},
			{
				'label': _('Pricing'),
				'items': ['Pricing Rule']
			},
		]
	}
"""
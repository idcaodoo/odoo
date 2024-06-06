# -*- coding: utf-8 -*-
{
    'name': 'Customer Info on Ticket',
    'version': '1.0',
    'author': 'IDCA',
    "sequence": 2,
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'summary': 'Add customer info in ticket format',
    'data': [
        'views/pos_config_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'custom_idca_ticket/static/src/js/order.js',
            'custom_idca_ticket/static/src/xml/order_receipt.xml',
        ],
    },
    'price': 0.0,
    'currency': "USD",
    'application': True,
    'installable': True,
    "auto_install": False,
    "license": "LGPL-3",
    "images":[],
}


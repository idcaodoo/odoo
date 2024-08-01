# -*- coding: utf-8 -*-
{
    'name': 'POS Receipt Print Format',
    'category': 'POS',
    'author': 'IDCA',
    'version': '1.0',
    'description': """Module help change pos ticket format""",
    'depends': ['point_of_sale'],
    'auto_install': True,
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_receipt_print/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
}

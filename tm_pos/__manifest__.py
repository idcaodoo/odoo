# -*- encoding: utf-8 -*-
{
    'name': 'TM: POS Restaurant',
    'version': '17.1',
    'author': 'IDCA',
    'summary': 'Module help custom POS Screen',
    'website': '',
    'category': 'POS',
    'description': """
    """,
    'sequence': 7,
    'depends': ['pos_restaurant', 'pos_preparation_display'],
    'data': [
        'data/res_partner_data.xml',
        'data/restaurant_floor_data.xml',
        'views/pos_order_views.xml'
    ],
    'images': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'tm_pos/static/src/js/*',
            "tm_pos/static/src/xml/*.xml"
        ],
        'pos_preparation_display.assets': [
            'tm_pos/static/src/app/*.xml',
            'tm_pos/static/src/app/*',
        ],
        'web.assets_backend': []
    },
    'installable': True,
    'application': False,
    'license': 'OPL-1',
}

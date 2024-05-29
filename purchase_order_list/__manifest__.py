# -*- encoding: utf-8 -*-
{
    'name': 'Purchase List Order',
    'version': '17.1',
    'author': 'IDCA',
    'summary': 'Module help custom Purchase Module',
    'website': '',
    'category': 'Purchase',
    'description': """
    """,
    'sequence': 55,
    'depends': ['purchase', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/res_partner_data.xml',
        'views/purchase_list_views.xml'
    ],
    'description': 'static/description/index.html',
    'images': [],
    'assets': {},
    'installable': True,
    'application': False,
    'license': 'OPL-1',
}

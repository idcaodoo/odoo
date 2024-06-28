# -*- encoding: utf-8 -*-
{
    "name": 'CFDI Bóveda fiscal',
    'license': 'GPL-3',
    "version": '17.1',
    "author": '...',
    "category": '',
    "website": "",
    "description": """Este módulo ...""",
    "depends": ['base', 'account_accountant'],
    "data": [
        'security/ir.model.access.csv',
        'reports/pack_qweb_report_view.xml',                        
        'views/cfdi_download_request_view.xml',
        'views/cfdi_download_fiel_view.xml',       
        'views/cfdi_download_pack_view.xml',
        'views/cfdi_download_data_view.xml',
        'views/account_move_views.xml',
        'wizard/request_wizard_view.xml',
    ],
    "external_dependencies": {
        "python": [
            "cfdiclient",
        ]
    },
    "installable": True,
    "auto_install": False,
}

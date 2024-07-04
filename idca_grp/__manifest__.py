{
    'name': 'IDCA GRP',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'GRP',
    'description': 'Módulo para la gestión GRP.',
    'author': 'IDCA',
    'depends': ['account_accountant','account_budget'],
    'data': [
        'security/ir.model.access.csv',
        'views/partida_presupuestaria_views.xml',
        'views/fondo_views.xml',
        'views/programa_views.xml',
        'views/finalidad_views.xml',
        'views/funcion_views.xml',
        'views/subfuncion_views.xml',
        'views/menu_views.xml',
        'views/crossovered_budget_lines_views.xml',

    ],
    'installable': True,
    'application': False,
}
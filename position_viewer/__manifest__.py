{
    'name': 'Position Viewer',
    'version': '1.0',
    'summary': 'Read-only viewer of positions and aggregated results imported from the course project via API token',
    'category': 'Human Resources',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/position_import_views.xml',
        'views/position_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}

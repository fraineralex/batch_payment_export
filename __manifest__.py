# __manifest__.py

{
    'name': 'Exportación de Pagos por Lote',
    'version': '1.0',
    'summary': 'Módulo para exportar pagos en lote a Excel',
    'description': 'Este módulo permite exportar pagos en lote a Excel.',
    'author': 'Lifer',
    'category': 'Accounting',
    'depends': ['base', 'account'],
    'data': [
        # views
        'views/ir.ui.menu.xml',

        # wizard views
        'wizard/batch_payment_wizard_view.xml',

        # security
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}

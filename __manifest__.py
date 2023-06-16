# __manifest__.py

{
    'name': 'Exportación de Pagos por Lote',
    'version': '1.0',
    'summary': 'Módulo para exportar pagos en lote a Excel',
    'description': 'Este módulo permite exportar pagos en lote a Excel.',
    'author': 'Lifter',
    'category': 'Accounting',
    'depends': ['dgii_reports'],
    'data': [
        # views
        'views/ir.ui.menu.xml',

        # wizard views
        'wizard/batch_payment_wizard_view.xml',

        # security
        'security/ir.model.access.csv',
    ],
    'icon': 'batch_payment_export/static/src/img/icon.png',
    'installable': True,
    'application': True,
    'auto_install': True,
    'license': 'LGPL-3',
}

# -*- coding: utf-8 -*-

from odoo import fields, models, _

class BatchPayment(models.Model):
    _name = 'batch.payment'
    _description = 'Batch Payments'

    account_number = fields.Char(string='Número de Cuenta')
    swift_code = fields.Char(string='Código SWIFT del Banco')
    account_type = fields.Selection([
        ('savings', 'Ahorros'),
        ('current', 'Corriente'),
    ], string='Tipo de Cuenta')
    beneficiary = fields.Char(string='Beneficiario')
    movement_type = fields.Selection([
        ('deposit', 'Depósito'),
        ('withdrawal', 'Retiro'),
    ], string='Tipo de Movimiento')
    amount = fields.Float(string='Monto')
    reference_number = fields.Char(string='Número de Referencia')
    description = fields.Text(string='Descripción')
    beneficiary_email = fields.Char(string='Correo del Beneficiario')
    beneficiary_phone = fields.Char(string='Teléfono del Beneficiario')
    identification_type = fields.Selection([
        ('passport', 'Pasaporte'),
        ('national_id', 'Cédula'),
        ('driver_license', 'Licencia de Conducir'),
    ], string='Tipo de Identificación')
    identification_number = fields.Char(string='Número de Identificación')
    transaction_reference = fields.Char(string='Referencia de Transacción')
    debit_reference = fields.Char(string='Referencia Débito')

    # Relational fields
    payment_type = fields.Integer(string='Tipo de Abono')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.ref('base.DOP').id)

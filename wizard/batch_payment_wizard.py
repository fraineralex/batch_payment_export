from odoo import models, fields
from xlwt import Workbook, easyxf
from odoo.exceptions import UserError
import base64
from werkzeug import urls
import io

# Valores por defecto
DEBIT_REFERENCE = ''
ABONO_TYPE = '1'
IDENTIFICATION_TYPE = {
    'CEDULA': 'C',
    'PASSPORT': 'P'
}

# constantes globales
INSTANT_PAYMENT = 1
SIMPLE_PAYMENT = 2


class BatchPaymentWizard(models.TransientModel):
    _name = 'batch.payment.wizard'
    _description = 'Wizard para generar reporte de pagos agrupados'

    payment_type = fields.Selection([
        ('instant_payment', 'Pago al Instante'),
        ('simple_payment', 'Pago Simple')
    ], string='Tipo de Pago', default='instant_payment')

    selected_payments = fields.Many2many(
        comodel_name='account.payment',
        relation='batch_payment_wizard_rel',
        column1='wizard_id',
        column2='payment_id',
        string='Pagos Seleccionados'
    )

    def generate_excel_report(self, headers, title, selected_payments, payment_type):
        # Crea el libro de Excel y la hoja de calculo
        workbook = Workbook()
        worksheet = workbook.add_sheet(title)
        excel_units = 256
        column_width = 20 * excel_units
        header_style = easyxf('font: bold on')

        for col_num, header in enumerate(headers):
            worksheet.col(col_num).width = column_width
            worksheet.write(0, col_num, header, header_style)

        for row_num, payment in enumerate(selected_payments, start=1):

            # Validaciones
            self.payment_validations(payment)

            # Campos requeridos del modelo en ambas plantillas
            reference_transaction = payment.move_id.name or ""
            account_number = payment.partner_bank_id.acc_number or ""
            beneficiary = payment.partner_bank_id.acc_holder_name or ""
            amount = str(payment.amount) or ""
            description = payment.ref or ""
            account_type = payment.partner_bank_id.acc_type or ""
            beneficiary_email = payment.partner_bank_id.partner_id.email or ""
            beneficiary_phone = payment.partner_bank_id.partner_id.phone or ""

            if payment_type == SIMPLE_PAYMENT:
                # Campos requeridos del modelo de pago para plantilla simple
                payment_type = ABONO_TYPE
                debit_reference = DEBIT_REFERENCE

                # Llenado de la hoja de excel
                worksheet.write(row_num, 0, payment_type)
                worksheet.write(row_num, 1, beneficiary)
                worksheet.write(row_num, 3, reference_transaction)
                worksheet.write(row_num, 2, amount)
                worksheet.write(row_num, 4, description)
                worksheet.write(row_num, 5, account_type)
                worksheet.write(row_num, 6, account_number)
                worksheet.write(row_num, 7, beneficiary_email)
                worksheet.write(row_num, 8, beneficiary_phone)
                worksheet.write(row_num, 9, debit_reference)

            elif payment_type == INSTANT_PAYMENT:
                # Campos requeridos del modelo de pago para plantilla de pago al instante
                swift_code = payment.partner_bank_id.bank_bic or ""
                movement_type = payment.move_id.type_name or ""
                identification_number = payment.partner_id.vat or ""
                identification_type = IDENTIFICATION_TYPE['CEDULA']

                # Llenado de la hoja de excel
                worksheet.write(row_num, 0, account_number)
                worksheet.write(row_num, 1, swift_code)
                worksheet.write(row_num, 2, account_type)
                worksheet.write(row_num, 3, beneficiary)
                worksheet.write(row_num, 4, movement_type)
                worksheet.write(row_num, 5, amount)
                worksheet.write(row_num, 6, reference_transaction)
                worksheet.write(row_num, 7, description)
                worksheet.write(row_num, 8, beneficiary_email)
                worksheet.write(row_num, 9, beneficiary_phone)
                worksheet.write(row_num, 10, identification_type)
                worksheet.write(row_num, 11, identification_number)

        return workbook

    def create_report(self):
        selected_payments = self.selected_payments
        payment_type = self.payment_type
        headers = []
        title = ''

        if payment_type == 'instant_payment':
            # Configurar los encabezados y título para el tipo de pago 'instant_payment'
            headers = [
                'Número de Cuenta', 'Código Swift', 'Tipo de Cuenta', 'Beneficiario', 'Tipo de Movimiento',
                'Monto', 'Número de Referencia', 'Descripción', 'Correo Beneficiario', 'Teléfono',
                'Tipo de Identificación', 'No. de Identificación'
            ]
            title = 'Reporte de Pagos al Instante'
            payment_type = INSTANT_PAYMENT
        elif payment_type == 'simple_payment':
            # Configurar los encabezados y título para el tipo de pago 'simple_payment'
            headers = [
                'Tipo de Abono', 'Beneficiario', 'Monto', 'Referencia de Transacción', 'Descripción',
                'Tipo de Cuenta', 'No. de Cuenta', 'Correo Beneficiario', 'Teléfono', 'Referencia de Débito'
            ]
            title = 'Reporte de Pago Simple'
            payment_type = SIMPLE_PAYMENT

        # Generar el reporte de Excel
        workbook = self.generate_excel_report(
            headers, title, selected_payments, payment_type)

        # Guardar el archivo de Excel en un objeto BytesIO
        workbook_data = io.BytesIO()
        workbook.save(workbook_data)
        workbook_data.seek(0)

        # Codificar el archivo de Excel en base64
        excel_base64 = base64.b64encode(workbook_data.getvalue())
        filename = urls.url_quote(title + '.xls')

        # Guardar el archivo adjunto en el registro del wizard
        report_file = excel_base64
        report_filename = filename

        # Devolver la acción de guardado para descargar el archivo
        return self.action_save(report_file, report_filename)

    def action_save(self, report_file, report_filename):
        # Crea un objeto Attachments para el archivo adjunto
        attachment = self.env['ir.attachment'].create({
            'name': report_filename,
            'datas': report_file,
            'mimetype': 'application/vnd.ms-excel',
            'res_model': self._name,
            'res_id': self.id,
        })

        # Devuelve la acción para descargar el archivo adjunto
        return {
            'name': 'Download',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def payment_validations(self, payment):
        # Si el monto es negativo o igual a cero
        error_message = ''
        if payment.amount <= 0:
            error_message = 'El monto del pago "{}" no puede ser negativo. Por favor, corrija el monto antes de continuar.'.format(
                payment.name)

        # Si el pago no tiene número de cuenta destino
        if not payment.partner_bank_id.acc_number:
            error_message = 'El pago "{}" debe contener un número de cuenta de destino. Por favor, agregue este campo antes de continuar.'.format(
                payment.name)

        # Si el pago no tiene beneficiario
        if not payment.partner_bank_id.acc_holder_name:
            error_message = 'El pago "{}" debe contener un beneficiario. Por favor, agregue este campo antes de continuar.'.format(
                payment.name)

        # Si el campo no tiene tipo de cuenta destino
        if not payment.partner_bank_id.acc_type:
            error_message = 'El pago "{}" debe contener un tipo de cuenta de destino. Por favor, agregue este campo antes de continuar.'.format(
                payment.name)

        if error_message != '':
            raise UserError(error_message)

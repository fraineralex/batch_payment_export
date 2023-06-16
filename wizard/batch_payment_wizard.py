from odoo import models, fields
from xlwt import Workbook
import base64
from werkzeug import urls
import io

class BatchPaymentWizard(models.TransientModel):
    _name = 'batch.payment.wizard'
    _description = 'Wizard para generar reporte de pagos agrupados'

    payment_type = fields.Selection([
        ('instant_payment', 'Pago al instante'),
        ('simple_template', 'Plantilla simple')
    ], string='Tipo de Pago', default='instant_payment')

    selected_payments = fields.Many2many(
        comodel_name='account.payment',
        relation='batch_payment_wizard_rel',
        column1='wizard_id',
        column2='payment_id',
        string='Pagos Seleccionados'
    )

    def generate_excel_report(self, headers, title, selected_payments):
        # Crea el libro de Excel
        workbook = Workbook()

        # Crea la hoja de trabajo
        worksheet = workbook.add_sheet(title)

        # Escribe los encabezados en la hoja de trabajo
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        for row_num, payment in enumerate(selected_payments, start=1):
            # Campos requeridos del modelo en ambas plantillas
            reference_transaction = payment.ref
            account_number = payment.partner_bank_id.acc_number
            beneficiary = payment.partner_bank_id.acc_holder_name
            amount = payment.amount
            description = payment.display_name #ojo
            account_type = payment.partner_bank_id.acc_type
            beneficiary_email = payment.partner_bank_id.partner_id.email
            beneficiary_phone = payment.partner_bank_id.partner_id.phone

            if title == 'Reporte de Plantilla Simple':
                # Campos requeridos del modelo de pago para plantilla simple
                payment_type = payment.payment_type
                debit_reference = payment.debit_origin_id.name

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

            elif title == 'Reporte de Pagos al Instante':
                # Campos requeridos del modelo de pago para plantilla de pago al instante
                swift_code = payment.partner_bank_id.bank_bic
                movement_type = payment.move_type
                identification_type = 'C' #ojo
                identification_number = '644543434543' #ojo

                # Llenado de la hoja de excel
                worksheet.write(row_num, 1, account_number)
                worksheet.write(row_num, 2, swift_code)
                worksheet.write(row_num, 3, account_type)
                worksheet.write(row_num, 4, beneficiary)
                worksheet.write(row_num, 5, movement_type)
                worksheet.write(row_num, 6, amount)
                worksheet.write(row_num, 7, reference_transaction)
                worksheet.write(row_num, 8, description)
                worksheet.write(row_num, 9, beneficiary_email)
                worksheet.write(row_num, 10, beneficiary_phone)
                worksheet.write(row_num, 11, identification_type)
                worksheet.write(row_num, 12, identification_number)

        return workbook

    def create_report(self):
        # Obtener los pagos seleccionados
        selected_payments = self.selected_payments

        # Obtener el tipo de pago elegido
        payment_type = self.payment_type

        # Definir los encabezados y el título del reporte
        headers = []
        title = ""

        if payment_type == 'instant_payment':
            # Configurar los encabezados y título para el tipo de pago "instant_payment"
            headers = [
                'Número de Cuenta', 'Código Swift', 'Tipo de Cuenta', 'Beneficiario', 'Tipo de Movimiento',
                'Monto', 'Número de Referencia', 'Descripción', 'Correo Beneficiario', 'Teléfono',
                'Tipo de Identificación', 'No. de Identificación'
            ]
            title = "Reporte de Pagos al Instante"
        elif payment_type == 'simple_template':
            # Configurar los encabezados y título para el tipo de pago "simple_template"
            headers = [
                'Tipo de Abono', 'Beneficiario', 'Monto', 'Referencia de Transacción', 'Descripción',
                'Tipo de Cuenta', 'No. de Cuenta', 'Correo Beneficiario', 'Teléfono', 'Referencia de Débito'
            ]
            title = "Reporte de Plantilla Simple"

        # Generar el reporte de Excel
        workbook = self.generate_excel_report(headers, title, selected_payments)

        # Guardar el archivo de Excel en un objeto BytesIO
        workbook_data = io.BytesIO()
        workbook.save(workbook_data)
        workbook_data.seek(0)

        # Codificar el archivo de Excel en base64
        excel_base64 = base64.b64encode(workbook_data.getvalue())

        # Establecer las cabeceras HTTP para la descarga del archivo
        content_type = 'application/vnd.ms-excel'
        filename = urls.url_quote(title + '.xls')
        content_disposition = f'attachment; filename="{filename}"'

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

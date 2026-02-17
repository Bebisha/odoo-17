import binascii
import tempfile
import xlrd
from odoo import models, fields, _
from odoo.exceptions import UserError


class GsmWizard(models.TransientModel):
    _name = "gsm.wizard"

    file = fields.Binary(string="File", required=True)
    gsm_id = fields.Many2one('gsm.details')

    def import_gsm_details(self):
        try:
            file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
            file_string.write(binascii.a2b_base64(self.file))
            book = xlrd.open_workbook(file_string.name)

        except:
            raise UserError(_("Please choose the .xlsx file"))
        for sheet in book.sheets():
            try:
                line_vals = []
                deduct_vals = []
                if sheet.name == 'Sheet1':
                    for row in range(sheet.nrows):
                        if row >= 1:
                            row_values = sheet.row_values(row)
                            employee = self.env['hr.employee'].search([('gsn_number', '=', row_values[0])])
                            if row_values[1] > employee.usage_limit:
                                line_vals.append((0, 0, {
                                    'gsm_no': row_values[0],
                                    'amount': row_values[1],
                                    'is_exceeds_or_not': True,
                                    'employee_id': employee.id,
                                    'exceeding_amount': row_values[1] - employee.usage_limit
                                }))
                                deduct_vals.append((0, 0, {
                                    'amount': row_values[1],
                                    'employee_id': employee.id,
                                }))
                            else:
                                line_vals.append((0, 0, {
                                    'gsm_no': row_values[0],
                                    'amount': row_values[1],
                                    'is_exceeds_or_not': False,
                                    'employee_id': employee.id,
                                    'exceeding_amount': 0
                                }))
                if line_vals:
                    self.gsm_id.write({
                        'line_ids': line_vals,
                        'deduct_ids': deduct_vals

                    })
            except IndexError:
                pass

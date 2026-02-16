from odoo import fields, models, api, _
from base64 import encodebytes
from datetime import datetime, timedelta
from io import BytesIO
from odoo.exceptions import ValidationError, UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PayslipReportWizard(models.TransientModel):
    _name = "payslip.report.wizard"
    _description = "Omani Staff Salary Statement"

    date_from = fields.Date()
    date_to = fields.Date()
    actual_deduction = fields.Boolean('Actual')
    expact_wiz = fields.Boolean('Expact')
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def print_sif_xlsx(self):

        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))

        if self.date_from and self.date_to:
            if self.date_from.month != self.date_to.month:
                raise UserError(_('The Payslip of the same month will be printed'))

        """ button action to print xlsx report of non UAE customers"""

        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {
            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.get_xlsx_report(workbook, data)
        workbook.close()
        fout = encodebytes(file_io.getvalue())
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'PaySlip Report'
        filename = '%s_%s' % (report_name, datetime_string)
        self.write({'fileout': fout, 'fileout_filename': filename})
        file_io.close()
        filename += '%2Exlsx'
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def get_xlsx_report(self, workbook, data, ):

        from_date = self.date_from
        to_date = self.date_to

        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center'})

        header_row_style = workbook.add_format({'bold': True, 'align': 'center', 'border': True})

        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '13px'})

        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})

        date_style = workbook.add_format(
            {'text_wrap': True, 'font_size': '10px', 'num_format': 'dd-mm-yyyy', 'align': 'left'})

        amt = workbook.add_format({'font_size': '10px', 'align': 'right'})

        bold = workbook.add_format({'bold': True, 'font_size': '8px', 'align': 'center'})

        sheet.set_column(1, 3, 20)
        sheet.set_column(0, 0, 20)
        sheet.set_row(2, 30)
        sheet.set_row(3, 30)
        sheet.set_column(4, 4, 25)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)
        sheet.set_column(12, 12, 15)
        sheet.set_column(13, 13, 20)
        sheet.set_column(14, 14, 15)
        sheet.set_column(15, 15, 15)
        sheet.set_column(16, 16, 15)
        sheet.set_column(17, 17, 15)
        sheet.set_column(18, 18, 15)
        sheet.set_column(19, 19, 20)
        sheet.set_column(20, 20, 15)
        sheet.set_column(21, 21, 15)
        sheet.set_column(22, 22, 25)
        sheet.set_column(23, 23, 15)

        sheet.set_column(26, 26, 15)
        sheet.set_column(27, 27, 15)
        sheet.set_column(28, 28, 15)
        sheet.write('B3', self.date_from, date_style)

        sheet.write('A4', 'Cost Center', bold)
        sheet.write('B4', 'Dept', bold)
        sheet.write('C4', 'Emp.No', bold)
        sheet.write('D4', 'Staff Name', bold)
        sheet.write('E4', 'Position.', bold)
        sheet.write('F4', 'Salary Days', bold)
        sheet.write('G4', 'Basic Salary', bold)
        sheet.write('H4', 'Housing Allowance', bold)
        sheet.write('I4', 'Transport Allowance', bold)
        sheet.write('J4', 'Utilities Allowance', bold)
        sheet.write('K4', 'Gross Income OMR', bold)
        sheet.write('L4', 'Gross Income USD', bold)
        sheet.write('M4', 'SSI 7% Employee', bold)
        sheet.write('N4', 'Job Security Employee 1%', bold)
        sheet.write('O4', 'Offshore Allowance', bold)
        sheet.write('P4', 'Other Allowance', bold)
        sheet.write('Q4', 'Special Payment', bold)
        sheet.write('R4', 'Net Payment', bold)
        sheet.write('S4', 'SSI Employer 10.5%', bold)
        sheet.write('T4', 'Job Security 1% Employer', bold)
        sheet.write('U4', 'SSI Employer 1%', bold)
        sheet.write('V4', 'Total SSI Company', bold)
        sheet.write('W4', 'Total SSI Company + Employee', bold)
        sheet.write('X4', 'Leave Deduction', bold)

        sheet.write('AA4', 'Other Deduction', bold)
        sheet.write('AB4', 'Reimbursements', bold)
        sheet.write('AC4', 'Final Total payable', bold)

        row = 4

        sheet.merge_range('A1:C1', 'Omani Staff Salary Statement', head)
        sheet.write('A3:B3', 'For the period of:', )

        payslip_obj = self.env['hr.payslip']
        if not self.expact_wiz:
            contracts = self.env['hr.contract'].search([('state', '=', 'open')])

            for contract in contracts:

                payslip_data = {
                    'employee_id': contract.employee_id.id,
                    'name': contract.employee_id.name,

                }

                payslip_id = payslip_obj.create(payslip_data)
                payslip_id.compute_sheet()

                total_h = []
                total_k = []

                sum_value = (
                        contract.wage +
                        contract.housing_allowance +
                        contract.transport_allowance +
                        contract.utilities_allowance
                )

                total_h.append(contract.housing_allowance)
                total_k.append(sum_value)

                sheet.write('D' + str(row + 1), payslip_id.employee_id.name, txt)
                sheet.write('E' + str(row + 1), payslip_id.employee_id.job_id.name or '', txt)
                sheet.write('F' + str(row + 1), 30 or '', txt)

                sheet.write('B' + str(row + 1), payslip_id.employee_id.department_id.name or '', txt)
                sheet.write('C' + str(row + 1), payslip_id.employee_id.registration_number or '', txt)
                sheet.write('G' + str(row + 1), contract.wage, amt)
                sheet.write('A' + str(row + 1), contract.analytic_account_id.name, txt)
                sheet.write('H' + str(row + 1), contract.housing_allowance, amt)
                sheet.write('I' + str(row + 1), contract.transport_allowance, amt)
                sheet.write('J' + str(row + 1), contract.utilities_allowance, amt)

                sheet.write('K' + str(row + 1), sum_value, amt)

                currency_rate = self.env['res.currency'].search([('name', '=', 'USD')], limit=1).rate
                sheet.write('L' + str(row + 1), sum_value * currency_rate, amt)

                sheet.write('M' + str(row + 1), sum_value * .07, amt)
                sheet.write('N' + str(row + 1), sum_value * .01, amt)
                sheet.write('O' + str(row + 1), contract.offshore_allowance, amt)
                sheet.write('P' + str(row + 1), contract.other_allowance, amt)

                net_payment = (sum_value + sum_value * 0.07 + sum_value * 0.01 + contract.offshore_allowance
                               + contract.other_allowance)
                sheet.write('R' + str(row + 1), net_payment, amt)

                sheet.write('S' + str(row + 1), sum_value * 10.5, amt)
                sheet.write('T' + str(row + 1), sum_value * .01, amt)
                sheet.write('U' + str(row + 1), sum_value * .01, amt)
                sheet.write('V' + str(row + 1), ((sum_value * 10.5) + (sum_value * .01) + (sum_value * .01)), amt)
                sheet.write('W' + str(row + 1),
                            ((sum_value * 10.5) + (sum_value * .01) + (sum_value * .01) + (sum_value * .07)), amt)

                total_net = net_payment - (((
                                                    contract.wage +
                                                    contract.housing_allowance +
                                                    contract.transport_allowance +
                                                    contract.utilities_allowance
                                            ) + (
                                                    contract.wage +
                                                    contract.housing_allowance +
                                                    contract.transport_allowance +
                                                    contract.utilities_allowance
                                            ) * 0.07 + (
                                                    contract.wage +
                                                    contract.housing_allowance +
                                                    contract.transport_allowance +
                                                    contract.utilities_allowance
                                            ) * 0.01 + contract.offshore_allowance
                                            + contract.other_allowance) / 30) * payslip_id.unpaid_days

                if self.actual_deduction == True:
                    sheet.write('X' + str(row + 1), total_net, amt)

                row += 1
                payslip_id.action_payslip_cancel()
                payslip_id.unlink()


        else:
            contracts = self.env['hr.contract'].search([('state', '=', 'open')])
            c_list = []
            # for contract in contracts:
            #     if contract.employee_id.expact_staff:
            #         c_list.append(contract.employee_id)

            for contract in contracts:
                if contract.employee_id.expact_staff:
                    c_list.append(contract.employee_id)

                if c_list:
                    if contract.employee_id.expact_staff:
                        payslip_data = {
                            'employee_id': contract.employee_id.id,
                            'name': contract.employee_id.name,

                        }
                        payslip_id = payslip_obj.create(payslip_data)
                        payslip_id.compute_sheet()
                        # wage = payslip_id.line_ids.filtered(lambda x:x.name == 'Basic Salary')

                        total_h = []
                        total_k = []

                        sum_value = (
                                contract.wage +
                                contract.housing_allowance +
                                contract.transport_allowance +
                                contract.utilities_allowance
                        )

                        total_h.append(contract.housing_allowance)
                        total_k.append(sum_value)

                        sheet.write('D' + str(row + 1), payslip_id.employee_id.name, txt)
                        sheet.write('E' + str(row + 1), payslip_id.employee_id.job_id.name or '', txt)
                        sheet.write('F' + str(row + 1), 30 or '', txt)

                        sheet.write('B' + str(row + 1), payslip_id.employee_id.department_id.name or '', txt)
                        sheet.write('C' + str(row + 1), payslip_id.employee_id.registration_number or '', txt)
                        sheet.write('G' + str(row + 1), contract.wage, amt)
                        sheet.write('A' + str(row + 1), contract.analytic_account_id.name, txt)

                        sheet.write('H' + str(row + 1), contract.housing_allowance, amt)
                        sheet.write('I' + str(row + 1), contract.transport_allowance, amt)
                        sheet.write('J' + str(row + 1), contract.utilities_allowance, amt)

                        sheet.write('K' + str(row + 1), sum_value, amt)

                        currency_rate = self.env['res.currency'].search([('name', '=', 'USD')], limit=1).rate
                        sheet.write('L' + str(row + 1), sum_value * currency_rate, amt)

                        sheet.write('M' + str(row + 1), sum_value * .07, amt)
                        sheet.write('N' + str(row + 1), sum_value * .01, amt)
                        sheet.write('O' + str(row + 1), contract.offshore_allowance, amt)
                        sheet.write('P' + str(row + 1), contract.other_allowance, amt)

                        net_payment = (sum_value + sum_value * 0.07 + sum_value * 0.01 + contract.offshore_allowance
                                       + contract.other_allowance)
                        sheet.write('R' + str(row + 1), net_payment, amt)

                        sheet.write('S' + str(row + 1), sum_value * 10.5, amt)
                        sheet.write('T' + str(row + 1), sum_value * .01, amt)
                        sheet.write('U' + str(row + 1), sum_value * .01, amt)
                        sheet.write('V' + str(row + 1), ((sum_value * 10.5) + (sum_value * .01) + (sum_value * .01)),
                                    amt)
                        sheet.write('W' + str(row + 1),
                                    ((sum_value * 10.5) + (sum_value * .01) + (sum_value * .01) + (sum_value * .07)),
                                    amt)

                        total_net = net_payment - (((
                                                            contract.wage +
                                                            contract.housing_allowance +
                                                            contract.transport_allowance +
                                                            contract.utilities_allowance
                                                    ) + (
                                                            contract.wage +
                                                            contract.housing_allowance +
                                                            contract.transport_allowance +
                                                            contract.utilities_allowance
                                                    ) * 0.07 + (
                                                            contract.wage +
                                                            contract.housing_allowance +
                                                            contract.transport_allowance +
                                                            contract.utilities_allowance
                                                    ) * 0.01 + contract.offshore_allowance
                                                    + contract.other_allowance) / 30) * payslip_id.unpaid_days

                        if self.actual_deduction == True:
                            sheet.write('X' + str(row + 1), total_net, amt)

                        row += 1
                        payslip_id.action_payslip_cancel()
                        payslip_id.unlink()

                else:

                    raise ValidationError(_("Oooops..There is no Expact Staff Registered"))

        # sheet.write('H' + str(row + 4), sum(total_h), amt)
        # sheet.write('K' + str(row + 4), sum(total_k), amt)

        workbook.close()

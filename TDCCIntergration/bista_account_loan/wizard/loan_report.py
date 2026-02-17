from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PayslipDetailsReport(models.AbstractModel):
    _name = 'report.bista_account_loan.report_loan'
    _description = 'Bista Account Loan Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'bista_account_loan.report_loan')
        loan_ids = self.get_data(data)

        return {
            'doc_ids': self.env["loan.report.print"].browse(data["ids"]),
            'doc_model': report.model,
            'docs': self.env['account.loan'].browse(loan_ids),
            'data': data,
        }

    def get_data(self, data):
        domain = []
        loan_ids = []
        from_date = (data.get('date_from'))
        to_date = (data.get('date_to'))
        # if data.get('employee_ids'):
        #     domain.append(('employee_id', 'in', data.get('employee_ids')))
        # if data.get('department_ids'):
        #     domain.append(
        #         ('department_id', 'in', data.get('department_ids')))
        for loan_rec in self.env['account.loan'].search(domain):
            loan_issuing_date = str(loan_rec.loan_issuing_date)
            if from_date <= loan_issuing_date <= to_date:
                loan_ids.append(loan_rec.id)
        if not loan_ids:
            raise ValidationError(_("No matching record found!"))
        return loan_ids


class LoanSummaryReport(models.AbstractModel):
    _name = 'report.bista_account_loan.report_loan_summary'
    _description = 'Finance Lease Summary'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'bista_account_loan.report_loan_summary')
        loan_ids = []
#         new_dept = []
        from_date = data.get('date_from')
        to_date = data.get('date_to')
        # for employee in data.get('employee_ids'):
        #     loan_rec = self.env['account.loan'].search([('employee_id', '=', employee), ('state', '=', 'approved')])
        #     for loan in loan_rec:
        #         loan_issuing_date = str(loan.loan_issuing_date)
        #         if loan_issuing_date >= from_date and loan_issuing_date <= to_date:
        #             loan_ids.append(loan)
        # for loan in loan_ids:
        #     if not loan.employee_id.department_id and loan.employee_id.department_id.id in new_dept:
        #         new_dept.append(loan.employee_id.department_id.id)
        # if not loan_ids:
        #     raise ValidationError(_("No matching record found!"))
        return {
            'doc_ids': self.env["loan.report.print"].browse(data["ids"]),
            'doc_model': report.model,
            'docs': loan_ids,
        }


class LoanReportPrint(models.Model):
    _name = 'loan.report.print'
    _description = 'Loan Report'

    company_id = fields.Many2one('res.company', string='Company')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    report_type = fields.Selection([('detail', 'Detailed'),
                                    ('summary', 'Summary')],
                                   copy=False,
                                   required=True,
                                   default='detail',
                                   string='Report Type')

    # @api.multi
    def check_loan_report(self):
        """
        get loan report line
        :return:
        """
        datas = {
            'ids': self.id,
            'date_from': self.date_from,
            'date_to': self.date_to,

        }
        return self.env.ref('bista_account_loan.action_loan_report'). \
            report_action(self, data=datas)

    # @api.multi
    def check_loan_report_summary(self):
        """
        get loan summary report
        :return:
        """

        datas = {
            'ids': self.id,
            'date_from': self.date_from,
            'date_to': self.date_to,

        }
        return self.env.ref('bista_account_loan.'
                            'action_loan_summmary_report'). \
            report_action(self, data=datas)

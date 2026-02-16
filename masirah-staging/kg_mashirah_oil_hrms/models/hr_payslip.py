from odoo import models, fields, api,_
from odoo.exceptions import AccessError, UserError, ValidationError



class KGHRPayslipInherit(models.Model):
    _inherit = "hr.payslip"

    flight_ticket_duration = fields.Integer(string="Air Ticket Duration")
    hotel_duration = fields.Integer(string="Hotel Duration")
    total_sick_leaves = fields.Integer(string="Total Sick Leaves")
    sick_deduction_amount = fields.Float('Sick Deduction Amount')
    offshore_duration = fields.Integer(string="Offshore Duration", compute='_compute_offshore_days')
    unpaid_days = fields.Integer(string="Unpaid Days",compute='get_unpaid_days')


    @api.onchange('employee_id', 'date_from', 'date_to')
    def get_emp_training_days(self):
        for rec in self:
            if rec.employee_id:
                emp_training_id = self.env['employee.training.form'].search(
                    [('employee_id', '=', rec.employee_id.id), ('state', '=', 'confirm')])

                air_ticket_dates = emp_training_id.filtered(lambda
                                                                x: x.training_from_date.date() >= rec.date_from and x.training_to_date.date() <= rec.date_to and x.air_ticket_request)
                rec.flight_ticket_duration = len(air_ticket_dates)

                hotel_dates = emp_training_id.filtered(lambda
                                                           x: x.training_from_date.date() >= rec.date_from and x.training_to_date.date() <= rec.date_to and x.hotel)
                rec.hotel_duration = len(hotel_dates)

                sick_leave_id = self.env.ref('hr_holidays.holiday_status_sl')
                hr_leave_id = self.env['hr.leave'].search(
                    [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', sick_leave_id.id),
                     ('state', '=', 'validate'), ('date_to', '<=', rec.date_to)])
                rec.total_sick_leaves = sum(hr_leave_id.mapped('number_of_days'))

                if rec.total_sick_leaves:
                    if rec.total_sick_leaves <= 21:
                        rec.sick_deduction_amount = 0.00

                    elif 22 <= rec.total_sick_leaves <= 35:
                        rec.sick_deduction_amount = rec.gross_wage * (75 / 100)

                    elif 36 <= rec.total_sick_leaves <= 70:
                        rec.sick_deduction_amount = rec.gross_wage * (50 / 100)

                    elif 71 <= rec.total_sick_leaves <= 182:
                        rec.sick_deduction_amount = rec.gross_wage * (25 / 100)
                else:
                    rec.sick_deduction_amount = 0.00

    def action_send_by_mail(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()
        lang = self.env.context.get('lang')
        mail_template = self._find_mail_template()
        if mail_template and mail_template.lang:
            lang = mail_template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'hr.payslip',
            'default_res_ids': self.ids,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
    def _find_mail_template(self):
        """ Get the appropriate mail template for the current PaySlip.

        If the PaySlip is confirmed, we return the mail template for the PaySlip confirmation.
        Otherwise, we return the PaySlip email template.

        :return: The correct mail template based on the current status
        :rtype: record of `mail.template` or `None` if not found
        """
        self.ensure_one()
        if self.env.context.get('proforma') :
            return self.env.ref('hr_payroll.email_template_edi_sale', raise_if_not_found=False)
        else:
            return self._get_confirmation_template()

    def _get_confirmation_template(self):
        """ Get the mail template sent on PaySlip confirmation (or for confirmed PaySlip).

        :return: `mail.template` record or None if default template wasn't found
        """
        self.ensure_one()
        default_confirmation_template_id = self.env['ir.config_parameter'].sudo().get_param(
            'hr_payroll.default_confirmation_template'
        )
        default_confirmation_template = default_confirmation_template_id \
            and self.env['mail.template'].browse(int(default_confirmation_template_id)).exists()
        if default_confirmation_template:
            return default_confirmation_template
        else:
            return self.env.ref('kg_mashirah_oil_hrms.mail_template_sale_confirmation', raise_if_not_found=False)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_offshore_days(self):
        for rec in self:
            offshore_days = self.env['hr.attendance'].search([('employee_id', '=', rec.employee_id.id),
                                                              ('offshore', '=', True),
                                                              ('check_in', '>=', rec.date_from),
                                                              ('check_out', '<=', rec.date_to)])
            rec.offshore_duration = False
            if offshore_days:
                rec.offshore_duration = len(offshore_days)

    @api.depends('employee_id', 'date_from', 'date_to')
    def get_unpaid_days(self):
        for payslip in self:
            unpaid_days = 0.0
            if payslip.employee_id:
                leave_domain = [
                    ('employee_id', '=', payslip.employee_id.id),
                    ('date_from', '<=', payslip.date_to),
                    ('date_to', '>=', payslip.date_from),
                ]
                leave_records = self.env['hr.leave'].search(leave_domain)
                unpaid_days = sum(leave.number_of_days_display for leave in leave_records)
            payslip.unpaid_days = unpaid_days
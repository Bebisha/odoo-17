from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EmployeeCertificates(models.Model):
    _name = "employee.certificates"
    _description = "Employee Certificate"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id)
    certificate = fields.Selection(
        [('exp', 'Experience Certificate'), ('concern', 'To Whom it may concern'), ('salary', 'Salary transfer letter'),
         ('status', 'Employee Status Letter'), ], string='Certificate Type')
    is_created = fields.Boolean(string='Created')
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    manager_id = fields.Many2one('hr.employee', compute='get_manager_id', default=False)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('employee.certificate.seq')
        vals['is_created'] = True
        return super(EmployeeCertificates, self).create(vals)

    def print_certificate_report(self):
        if self.certificate:
            if self.certificate == 'exp':
                action = self.env.ref('kg_mashirah_oil_hrms.kg_experience_cert_with_seq')
            elif self.certificate == 'concern':
                action = self.env.ref('kg_mashirah_oil_hrms.kg_to_whom_it_may_concern_seq')
            elif self.certificate == 'salary':
                action = self.env.ref('kg_mashirah_oil_hrms.kg_salary_transfer_with_seq')
            else:
                action = self.env.ref('kg_mashirah_oil_hrms.kg_employement_status')
            return action.read()[0]
        else:
            raise UserError("Please select Certificate type")

    def get_manager_id(self):
        '''Getting the manager field value from the res_config_settings'''
        manager_id = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_hrms.manager_id', default=False)
        self.manager_id = int(manager_id)

from odoo import models, fields, api, _
from odoo.osv import expression


class KGHREMPLOYEE(models.Model):
    _inherit = "hr.employee"

    passport_exp_date = fields.Date(string="Passport Expiration Date")
    date_of_join = fields.Date(string="Date Of Join")
    clearance_certi = fields.Many2many('ir.attachment', relation='certificate_rel', string="Clearance Certificate")
    civil_id = fields.Many2many('ir.attachment', relation='civil_rel', string="Civil Id")
    medical = fields.Many2many('ir.attachment', string="Medical")

    emp_civil_num = fields.Char(string="Employee Civil Number")
    emp_contract_masirah = fields.Many2many('ir.attachment', relation='emp_contract_masirah_rel',
                                            string="Employee Contract(Masirah Oil)")
    emp_contract_labor = fields.Many2many('ir.attachment', relation='emp_contract_labor_rel'
                                          , string="Employee Contract(Ministry Of Labor)")
    religion_id = fields.Many2one("hr.religion", string="Religion")
    grade_id = fields.Char('Job Grade', compute='_compute_grade_id', readonly=True)
    expact_staff = fields.Boolean(string="Expact Staff")
    sign_signature = fields.Binary(string="Digital Signature", copy=False)
    arabic_name = fields.Char('Arabic Name', copy=False, store=True)
    arabic_job_name = fields.Char('Arabic Job Name', copy=False, store=True)

    @api.depends('job_id')
    def _compute_grade_id(self):
        for rec in self:
            rec.grade_id = rec.job_id.grade_id.name

    def action_open_payslips_emp(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hr_payroll.action_view_hr_payslip_month_form")
        action.update({'domain': [('contract_id', '=', self.contract_id.id)]})
        return action

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if operator != 'ilike' or (name or '').strip():
            name_domain = ['|', ('name', 'ilike', name), ('registration_number', 'ilike', name)]
            domain = expression.AND([name_domain, domain])
        return self._search(domain, limit=limit, order=order)


class KgHrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    def action_open_payslips_emp(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hr_payroll.action_view_hr_payslip_month_form")
        action.update({'domain': [('employee_id', '=', self.employee_id.id)]})
        return action


class KGRESBANK(models.Model):
    _inherit = "res.partner.bank"

    iban = fields.Char(string="IBAN")
    bic = fields.Char(string="BIC(swift code)")

from odoo import models, fields, api, _
import random
import string


class Insurance(models.Model):
    _name = 'insurance.form'

    in_company_name = fields.Char(string="Insurance Company Name")
    health_plan_id = fields.Char(string="Health Plan ID")
    insurence_compny_id = fields.Char(string="Insurance Company ID")
    insured_name = fields.Char(string="Insured Name")
    company_des = fields.Char(string="Text")

    policy_no = fields.Char(string="Policy Number", help="Membership Number or Policy Number")
    insurance_id  = fields.Many2one('res.partner', string='Student')
    effective_date = fields.Datetime(string="Effective Date")
    expiration_date = fields.Datetime(string="Expiration Date")

    set_id_inr = fields.Char(string='Set ID – INR ', copy=False, index=True, readonly=False,
                             default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        if vals.get('set_id_inr', _('New')) == _('New'):
            vals['set_id_inr'] = self.env['ir.sequence'].next_by_code(
                'set_id_inr') or _('New')
        return super(Insurance, self).create(vals)
from odoo import models, fields, _, api


class GsmDetails(models.Model):
    _name = "gsm.details"

    gsm_name = fields.Char("Name")
    name = fields.Char('Sequence')
    line_ids = fields.One2many('gsm.details.line', 'line_id')
    deduct_ids = fields.One2many('salary.deduct.line', 'deduct_id')
    from_date = fields.Date('From')
    to_date = fields.Date('To')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('gsm.details') or _('New')
        res = super(GsmDetails, self).create(vals)
        return res

    def import_gsm_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'gsm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_gsm_id': self.id}
        }


class GsmDetailsLine(models.Model):
    _name = "gsm.details.line"

    line_id = fields.Many2one('gsm.details')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    gsm_no = fields.Integer('GSM No.')
    is_exceeds_or_not = fields.Boolean('Exceeds or not', default=False)
    amount = fields.Float('Amount')
    exceeding_amount = fields.Float('Exceeding Amount')


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()
        for record in self:
            # record.input_line_ids = False
            gsm = self.env['gsm.details'].search([('from_date', '=', record.date_from),
                                                  ('to_date', '=', record.date_to),
                                                  ])

            for rec in gsm.deduct_ids:
                if rec.employee_id.id == record.employee_id.id:
                    rec.related_payslip_id = record.id
                    line_vals = []
                    line_vals.append((0, 0, {
                        'input_type_id': 1,
                        'name': 'Deduction from GSM Bill',
                        'amount': rec.amount
                    }))
                    record.write({
                        'input_line_ids': line_vals,
                    })
        return res


class SalaryDeductLine(models.Model):
    _name = "salary.deduct.line"

    deduct_id = fields.Many2one('gsm.details')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    amount = fields.Float('Amount')
    related_payslip_id = fields.Many2one('hr.payslip')

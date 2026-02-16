from odoo import models, fields, api, _


class KGJobGrade(models.Model):
    _name = 'job.grade'

    name = fields.Char('Job Grade', required=True)
    grade_code = fields.Char(copy=False, readonly=True, index=True,
                             default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        if vals.get('grade_code', _('New')) == _('New'):
            vals['grade_code'] = self.env['ir.sequence'].next_by_code(
                'job.grade.seq') or _('New')
        res = super(KGJobGrade, self).create(vals)
        return res

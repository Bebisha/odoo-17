from odoo import fields, models, api,_


class ZSegmentSocialHistory(models.Model):
    _name = "segment.social.history"

    social_habits = fields.Many2one('social.habit',string="Social Habit", help="Social Habit Code--- Smoking",default= lambda self: self.env['social.habit'].search([('code', '=', 'Smoking')], limit=1) )
    social_habit_categorys = fields.Many2one('social.habit.category',string="Social Habit Category",default= lambda self: self.env['social.habit.category'].search([('code', '=', 'Smoking')], limit=1))
    social_habit_qty = fields.Char(string="Social Habit Qty" , default ="Medium")
    social_habit_qty_id = fields.Many2one('social.habit.qty',string="Social Habit Qty")
    segment_family_social_id = fields.Many2one('res.partner', string='Student')
    set_id_ssh = fields.Char(string='Set ID – ZSH ', copy=False, index=True, readonly=False,
                             default=lambda self: _('New'))
    from_date = fields.Datetime(string="From Date")
    to_date = fields.Datetime(string="To Date")

    @api.model
    def create(self, vals):
        if vals.get('set_id_ssh', _('New')) == _('New'):
            vals['set_id_ssh'] = self.env['ir.sequence'].next_by_code(
                'set_id_ssh') or _('New')
        return super(ZSegmentSocialHistory, self).create(vals)
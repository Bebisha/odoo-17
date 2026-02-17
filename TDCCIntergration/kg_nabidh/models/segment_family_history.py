from odoo import fields, models, api,_


class KgZSegmentFamilyHistory(models.Model):
    _name = "segment.family.history"


    fam_member_name=fields.Char(string="Family members name")
    status = fields.Selection([('Active', 'A'), ('Inactivate', 'I')],
                              help="A for ‘Active’ or I for ‘Inactive",
                              string="Status")
    segment_family_history_id = fields.Many2one('res.partner', string='Student')

    set_id_zfh = fields.Char(string='Set ID – ZFH ', copy=False, index=True, readonly=False,
                             default=lambda self: _('New'))
    from_date = fields.Datetime(string="From Date")
    to_date = fields.Datetime(string="To Date")

    @api.model
    def create(self, vals):
        if vals.get('set_id_zfh', _('New')) == _('New'):
            vals['set_id_zfh'] = self.env['ir.sequence'].next_by_code(
                'set_id_zfh') or _('New')
        return super(KgZSegmentFamilyHistory, self).create(vals)
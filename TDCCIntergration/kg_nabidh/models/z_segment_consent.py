from odoo import fields, models, api,_


class ZSegmentConsent(models.Model):
    _name = "z.segment.consent"


    is_opted = fields.Selection([('true', 'True'), ('false', 'False')], 'Is Opted',
                              default='true')
    segment_family_consent_id = fields.Many2one('res.partner', string='SegmentConsent')
    facility_from_date = fields.Datetime('Facility Date')
    global_from_date = fields.Datetime('Global Date')


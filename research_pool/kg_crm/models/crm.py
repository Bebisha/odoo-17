from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    lead_source = fields.Selection([
        ('campaign', 'Campaign'),
        ('website', 'Website'),
        ('recommendation', 'Recommendation'),
        ('other', 'Other')
    ], string='Lead Source', default='campaign')

    def action_pp(self):
        print("iiiiiiiiiiiiiii")

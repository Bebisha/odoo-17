from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    teams_id = fields.Many2one("helpdesk.ticket.team", 'Teams')

    helpdesk_user_ids = fields.Char(
        string="Helpdesk User Email"
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    teams_id = fields.Many2one("helpdesk.ticket.team", 'Teams',
                               readonly=False, related="company_id.teams_id")

    helpdesk_user_ids = fields.Char(
        related="company_id.helpdesk_user_ids",
        string="Helpdesk User Email",
        readonly=False
    )




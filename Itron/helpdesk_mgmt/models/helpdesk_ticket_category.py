from odoo import fields, models,api


class HelpdeskCategory(models.Model):

    _name = "helpdesk.ticket.category"
    _description = "Helpdesk Ticket Category"

    active = fields.Boolean(default=True, )
    name = fields.Char(required=True, translate=True, )
    company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company, )
    user_ids = fields.Many2many(comodel_name="res.users",string="Users")


class HelpdeskApplication(models.Model):
    _name = "helpdesk.ticket.application"
    _description = "Helpdesk Ticket Application"

    active = fields.Boolean(default=True,)
    name = fields.Char(required=True,translate=True,)
    company_id = fields.Many2one(comodel_name="res.company",string="Company",default=lambda self: self.env.company,)
    user_ids = fields.Many2many(comodel_name="res.users",string="Users")
    # team_id = fields.Many2one(
    #     comodel_name='helpdesk.ticket.team',
    #     string='Team Id')

    team_id = fields.Many2one('helpdesk.ticket.team', string='Team Id', required=True,
                              domain=lambda self: self._compute_team_domain())

    @api.model
    def _compute_team_domain(self):
        if self.env.user.has_group('base.group_multi_company'):
            return [('company_id', '=', self.company_id.id)]
        else:
            return []

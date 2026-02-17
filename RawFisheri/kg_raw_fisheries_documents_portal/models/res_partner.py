from odoo import models, api
from odoo.exceptions import ValidationError


class KGPortalResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        res = super(KGPortalResPartner, self).create(vals)
        if res and not res.user_ids and res.customer_rank > 0:
            if not res.email:
                raise ValidationError("Enter the email !")
            user = self.env['res.users'].create({
                'name': res.name,
                'partner_id': res.id,
                'groups_id': self.env.ref('base.group_portal'),
                'login': res.email
            })
            if user:
                user.action_reset_password()
        return res

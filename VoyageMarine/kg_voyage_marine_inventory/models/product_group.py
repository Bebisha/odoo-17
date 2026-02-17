from odoo import models, fields, _
from odoo.exceptions import UserError


class KGProductGroup(models.Model):
    _name = "product.group"
    _description = "Product Group"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    code = fields.Char(string="code")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    no_delete = fields.Boolean(default=False, string="No Delete")

    # def unlink(self):
    #     for group in self:
    #         if group.no_delete:
    #             raise UserError(_("You cannot delete the product group '%s'." % group.name))
    #
    #     return super(KGProductGroup, self).unlink()

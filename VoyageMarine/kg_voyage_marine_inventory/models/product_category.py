from odoo import models, fields, _
from odoo.exceptions import UserError



class KGProductCategory(models.Model):
    _inherit = 'product.category'

    code = fields.Char(string="Code")
    product_group_id = fields.Many2one("product.group", string="Product Group")
    no_delete = fields.Boolean(default=False, string="No Delete")
    is_scope = fields.Boolean(string="IS Scope")

    # def unlink(self):
    #     for category in self:
    #         if category.no_delete:
    #             raise UserError(_("You cannot delete the category '%s'." % category.name))
    #
    #     return super(KGProductCategory, self).unlink()

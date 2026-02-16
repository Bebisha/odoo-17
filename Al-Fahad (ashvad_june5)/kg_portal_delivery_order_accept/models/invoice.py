from odoo import api, models, fields
from odoo.exceptions import AccessError
from odoo.http import request


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    warehouse_id = fields.Many2one('stock.warehouse', related='location_id.warehouse_id')
    boolean = fields.Boolean('Bool')

    # @api.model
    # def create(self, values):
    #     # Check if the user belongs to any of the allowed groups
    #     allowed_groups = ['base.group_extra_rights', 'stock.group_stock_manager', 'purchase.group_purchase_manager',
    #                       'purchase.group_purchase_user', 'sales_team.group_sale_manager',
    #                       'sales_team.group_sale_salesman_all_leads',
    #                       'base.group_user']
    #     if self.env.user.has_group(any(allowed_groups)):
    #         return super(StockPicking, self).create(values)
    #     else:
    #         # Raise an error if the user doesn't have the necessary access rights
    #         raise AccessError("You are not allowed to create inventory locations.")
    #
    # @api.multi
    # def write(self, values):
    #     # Check if the user belongs to any of the allowed groups
    #     allowed_groups = ['base.group_extra_rights', 'stock.group_stock_manager', 'purchase.group_purchase_manager',
    #                       'purchase.group_purchase_user', 'sales_team.group_sale_manager',
    #                       'sales_team.group_sale_salesman_all_leads',
    #                       'base.group_user']
    #     if self.env.user.has_group(any(allowed_groups)):
    #         return super(StockPicking, self).write(values)
    #     else:
    #         # Raise an error if the user doesn't have the necessary access rights
    #         raise AccessError("You are not allowed to modify inventory locations.")
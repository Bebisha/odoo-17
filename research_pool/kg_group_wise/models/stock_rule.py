# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models,fields,api

class StockRule(models.Model):
    """By inheriting this model generating corresponding product's stock
     moves."""
    _inherit = 'stock.rule'

    branch_id = fields.Many2one('kg_branch', string="Branch")

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, company_id, values):
        """Retrieve stock move values for a given product."""
        if values.get('sale_line_id', False):
            sale_line_id = self.env['sale.order.line'].sudo().browse(values['sale_line_id'])
            self.location_src_id = sale_line_id.branch_id.id \
                if sale_line_id.branch_id \
                else self.picking_type_id.default_location_src_id

        return super()._get_stock_move_values(product_id,
                                              product_qty,
                                              product_uom,
                                              location_id,
                                              name, origin,
                                              company_id,
                                              values)

    # @api.model
    # def _run_pull(self, procurements):
    #     for procurement, rule in procurements:
    #         move_values = rule._get_stock_move_values(*procurement)
    #         sale_line_id = self.env['sale.order.line'].sudo().browse(move_values['sale_line_id'])
    #         move_values['branch_id'] = sale_line_id.branch_id.id
    #     return super()._run_pull(self, procurements)


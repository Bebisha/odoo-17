import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression


class KGProductProductInherit(models.Model):
    _inherit = "product.product"

    @api.model
    def default_get(self, fields):
        result = super(KGProductProductInherit, self).default_get(fields)
        if not self._context.get('default_detailed_type'):
            result['detailed_type'] = 'product'
        if result.get("is_equipment"):
            result["product_group_id"] = self.env.ref(
                "kg_voyage_marine_inventory.group_cal_categ_system"
            ).id
            result["categ_id"] = []

        return result

    is_equipment = fields.Boolean(string="Equipment", help="Check this box if the item is considered equipment.")
    show_onhand = fields.Float(string='This Year On Hand', store=True)

    this_year_onhand = fields.Float(string='On Hand This Year', compute='_compute_this_year_onhand')
    this_year_incoming = fields.Float(string='Incoming This Year', compute='_compute_this_year_incoming')
    this_year_outgoing = fields.Float(string='Outgoing This Year', compute='_compute_this_year_outgoing', )


    @api.onchange("is_equipment")
    def _onchange_is_equipment(self):
        if self.is_equipment:
            group_id = self.env.ref("kg_voyage_marine_inventory.group_cal_categ_system").id
            return {"domain": {"categ_id": [("parent_id.group_id", "=", group_id)]}}
        else:
            return {"domain": {"categ_id": []}}

    def _compute_this_year_onhand(self):
        current_year = fields.Date.today().year
        for product in self:
            if product.this_year_incoming or product.this_year_outgoing:
                product.this_year_onhand = product.this_year_incoming - product.this_year_outgoing
                product.show_onhand = product.this_year_incoming - product.this_year_outgoing
            else:
                product.this_year_onhand = 0
                product.show_onhand = 0

    def _compute_this_year_incoming(self):
        current_year = fields.Date.today().year
        start_date = f'{current_year}-01-01'
        end_date = f'{current_year}-12-31'
        for product in self:
            stock_quants = self.env['stock.move.line'].search([
                ('product_id', '=', product.id),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('state', '=', 'done'),
                ('location_usage', '!=', ('internal', 'transit')),
                ('location_dest_usage', '=', ('internal', 'transit')),

            ])
            total_incomming = sum(stock_quants.mapped('quantity'))
            if total_incomming:
                product.this_year_incoming = total_incomming
            else:
                product.this_year_incoming = 0

    def _compute_this_year_outgoing(self):
        current_year = fields.Date.today().year
        start_date = f'{current_year}-01-01'
        end_date = f'{current_year}-12-31'
        for product in self:
            stock_quants = self.env['stock.move.line'].search([
                ('product_id', '=', product.id),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('state', '=', 'done'),
                ('location_usage', '=', ('internal', 'transit')),
                ('location_dest_usage', '!=', ('internal', 'transit')),
                # ('picking_code', '=', 'outgoing'),
            ])
            total_outgoing = sum(stock_quants.mapped('quantity'))  # or 'quantity', based on your actual field
            product.this_year_outgoing = total_outgoing if total_outgoing else 0

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = list(self._search([('default_code', '=', name)] + domain, limit=limit, order=order))
                if not product_ids:
                    product_ids = list(self._search([('barcode', '=', name)] + domain, limit=limit, order=order))
                if not product_ids:
                    product_ids = list(self._search([('existing_code', '=', name)] + domain, limit=limit, order=order))

            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                product_ids = list(self._search(domain + [('default_code', operator, name)], limit=limit, order=order))
                if not limit or len(product_ids) < limit:
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(
                        domain + [('name', operator, name), ('id', 'not in', product_ids)], limit=limit2, order=order
                    )
                    product_ids.extend(product2_ids)
                if not limit or len(product_ids) < limit:
                    limit3 = (limit - len(product_ids)) if limit else False
                    product3_ids = self._search(
                        domain + [('existing_code', operator, name), ('id', 'not in', product_ids)], limit=limit3,
                        order=order
                    )
                    product_ids.extend(product3_ids)

            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain2 = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain2 = expression.AND([domain, domain2])
                product_ids = list(self._search(domain2, limit=limit, order=order))

            if not product_ids and operator in positive_operators:
                ptrn = re.compile(r'(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = list(
                        self._search([('default_code', '=', res.group(2))] + domain, limit=limit, order=order)
                    )
            if not product_ids and self._context.get('partner_id'):
                suppliers_ids = self.env['product.supplierinfo']._search([
                    ('partner_id', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)
                ])
                if suppliers_ids:
                    product_ids = self._search(
                        [('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit, order=order
                    )
        else:
            product_ids = self._search(domain, limit=limit, order=order)
        return product_ids

# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.misc import unique


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')

    @api.depends('name', 'default_code', 'uom_id')
    def _compute_display_name(self):
        for template in self:
            if not template.name:
                template.display_name = False
            else:
                parts = []
                if template.default_code:
                    parts.append(template.default_code)
                if template.uom_id:
                    parts.append(template.uom_id.name)
                prefix = f"[{', '.join(parts)}] " if parts else ''
                template.display_name = f"{prefix}{template.name}"

class ProductProduct(models.Model):
    _inherit = 'product.product'

    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel', related='product_tmpl_id.vessel_id')

    @api.depends('name', 'default_code', 'product_tmpl_id', 'uom_id')
    @api.depends_context('display_default_code', 'seller_id', 'company_id', 'partner_id', 'use_partner_name')
    def _compute_display_name(self):
        def get_display_name(name, code, uom):
            parts = []
            if self._context.get('display_default_code', True) and code:
                parts.append(code)
            if uom:
                parts.append(uom)
            prefix = f"[{', '.join(parts)}] " if parts else ""
            return f"{prefix}{name}"

        partner_id = self._context.get('partner_id') if self.env.context.get('use_partner_name', True) else self.env[
            'res.partner']
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        self.check_access_rights("read")
        self.check_access_rule("read")

        product_template_ids = self.sudo().product_tmpl_id.ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search_fetch(
                [('product_tmpl_id', 'in', product_template_ids), ('partner_id', 'in', partner_ids)],
                ['product_tmpl_id', 'product_id', 'company_id', 'product_name', 'product_code'],
            )
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)

        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()
            name = f"{product.name} ({variant})" if variant else product.name

            sellers = self.env['product.supplierinfo'].sudo().browse(self.env.context.get('seller_id')) or []
            if not sellers and partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]

            if sellers:
                temp = []
                for s in sellers:
                    seller_variant = s.product_name and (
                        f"{s.product_name} ({variant})" if variant else s.product_name) or False
                    display = get_display_name(seller_variant or name, s.product_code or product.default_code,
                                               product.uom_id.name if product.uom_id else "")
                    temp.append(display)
                product.display_name = ", ".join(unique(temp))
            else:
                product.display_name = get_display_name(name, product.default_code,
                                                        product.uom_id.name if product.uom_id else "")
import html
import re

from odoo.exceptions import ValidationError
from odoo import models, fields, _


class DNSelectProducts(models.TransientModel):
    _name = "dn.select.products"
    _description = "DN Select Products"

    name = fields.Char(string="Reference")
    product_ids = fields.Many2many("product.product", 'dn_products_rel', string="Select Products")
    dn_product_ids = fields.Many2many("product.product", string="DN Products")
    picking_id = fields.Many2one("stock.picking", string="Transfer")
    so_id = fields.Many2one("sale.order", string="SO")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, string="Company")

    def print_dn_report(self):
        vals = []
        if self.so_id:
            for prod in self.product_ids:
                sol_ids = self.so_id.order_line.filtered(lambda x: x.product_id.id == prod.id)
                qty_delivered = sum(sol_ids.mapped('qty_delivered'))
                if qty_delivered:
                    description = "\n".join(sol_ids.mapped('name'))
                    lines = {
                        'product': prod.name,
                        'description': description,
                        'qty': qty_delivered,
                        'uom': prod.uom_id.name
                    }
                    vals.append(lines)

        if not vals:
            raise ValidationError(_('No data in this date range'))

        data = {
            'company_logo': self.company_id.logo,
            'company_name': self.company_id.name,
            'company_phone': self.company_id.phone,
            'company_mobile': self.company_id.mobile,
            'company_email': self.company_id.email,
            'company_zip': self.company_id.zip,
            'company_city': self.company_id.city,
            'company_state': self.company_id.state_id.name,
            'company_country_code': self.company_id.country_id.name,
            'company_vat': self.company_id.vat,
            'company_website': self.company_id.website,

            'vessel_name': self.so_id.vessel_id.name,
            'picking_name': self.picking_id.name,
            'customer_ref': self.so_id.customer_reference,
            'scheduled_date': self.so_id.date_order,
            'so_ids': self.so_id.name,
            'po_ids': ",".join(self.so_id.po_ids.mapped("name")) if self.so_id.po_ids else "",
            'note': self.so_id.note if self.so_id.note else False,

            'partner_name': self.so_id.partner_id.name,
            'partner_street': self.so_id.partner_id.street,
            'partner_street2': self.so_id.partner_id.street2,
            'partner_city': self.so_id.partner_id.city,
            'partner_zip': self.so_id.partner_id.zip,
            'partner_state': self.so_id.partner_id.state_id.name,
            'partner_country_code': self.so_id.partner_id.country_id.code,
            'job_delivery_note':self.so_id.opportunity_id.job_delivery_note if self.so_id.opportunity_id.job_delivery_note else self.so_id.estimation_id.opportunity_id.job_delivery_note,
            'values': vals
        }

        return self.env.ref('kg_voyage_marine_inventory.kg_delivery_note_report').with_context(
            landscape=False).report_action(self, data=data)

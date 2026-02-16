# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class KGProductTemplate(models.Model):
    _inherit = 'product.template'

    is_pack = fields.Boolean(string='Is Product Pack')
    pack_ids = fields.One2many('product.pack.line', 'product_tmp_id',
                               'Product Pack')
    pricelist_type = fields.Selection([('eip', 'EIP'),
                                       ('eiip', 'Intensive Program'),
                                       ('360', '360'),
                                       ('taaleem', 'Taaleem')],
                                      string='Pricelist Type')


class KGProductPackLine(models.Model):
    _name = 'product.pack.line'
    _description = 'Product Pack LIne'

    product_id = fields.Many2one('product.product',
                                 string='Products')
    price = fields.Float(string='Price')
    product_tmp_id = fields.Many2one(
        'product.template',
        string='Product template')


class KGSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange('product_id')
    def product_id_change(self):
        context = dict(self._context)
        res = {}  # Initialize res
        if context.get('from_pack_product'):
            product_tmpl_ids = self.env['product.template'].search([
                ('is_pack', '=', True)])
            product_ids = self.env['product.product'].search([
                ('product_tmpl_id', 'in', product_tmpl_ids.ids)])
            res['domain'] = {'product_id': [('id', 'in', product_ids.ids)]}
        return res


class KGSaleOrder(models.Model):
    _inherit = "sale.order"

    def action_product_pack(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.pack.wizard',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Product Pack',
            # 'context': {'default_product_id': self.id}
        }


class KGAccountMove(models.Model):
    _inherit = "account.move"

    def action_invoice_product_pack(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.product.pack.wizard',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Product Pack',
            'context': {'default_product_id': self.id}
        }
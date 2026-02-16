from odoo import models, fields, api


class PurchaseOrderRevised(models.Model):
    _name = 'po.revised'
    _rec_name = 'revised_number'
    _description = 'Purchase Order Revised'

    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase order',
    )
    revised_number = fields.Char(
        string='Revision Number',
        readonly=True,
    )
    revised_line_ids = fields.One2many(
        'poline.revised',
        'line_custom_id',
        string='Revision Purchase Line',
        readonly=True,

    )
    sale_person_id = fields.Many2one(
        'res.users',
        string='Sales Person',
        related='purchase_order_id.user_id',
        store=True,
    )

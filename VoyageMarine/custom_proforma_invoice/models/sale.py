
from odoo import models, fields,  api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    proforma_id = fields.Many2one('custom.proforma.invoice', string="Proforma Invoice")
    proforma_status = fields.Selection([
        ('draft', 'Not Created'),
        ('proforma_created', 'Proforma Created'),
        ('proforma_sent', 'Proforma Sent'),
    ], string='Proforma Status', default='draft', tracking=True)

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_proforma_as_sent'):
            self.write({'proforma_status': 'proforma_sent'})
            self.proforma_id.write({'state': 'sent'})
        return super().message_post(**kwargs)

    def action_create_proforma(self):
        self.ensure_one()

        proforma_obj = self.env['custom.proforma.invoice'].create({
            'sale_order_id': self.id,
        })
        self.proforma_id = proforma_obj.id
        self.proforma_status = 'proforma_created'

        return {
            'type': 'ir.actions.act_window',
            'name': 'Proforma Invoice',
            'res_model': 'custom.proforma.invoice',
            'view_mode': 'form',
            'res_id': proforma_obj.id,
            'target': 'current',
        }

    proforma_count = fields.Integer(
        string='Proforma Count',
        compute='_compute_proforma_count'
    )

    def _compute_proforma_count(self):
        for order in self:
            order.proforma_count = self.env['custom.proforma.invoice'].search_count([
                ('sale_order_id', '=', order.id)
            ])

    def action_view_proforma(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Proforma Invoice',
            'res_model': 'custom.proforma.invoice',
            'view_mode': 'tree,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {
                'default_sale_order_id': self.id
            },
        }


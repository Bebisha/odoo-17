#    Stranbys Info Solution. Ltd.
#    ===========================
#    Copyright (C) 2022-TODAY Stranbys Stranbys Info Solution(<https://www.stranbys.com>)
#    Author: Stranbys Info Solution(<https://www.stranbys.com>)
from odoo import fields, models, _


class KGPurchaseRevision(models.TransientModel):
    _name = 'purchase.order.revision.wizard'

    order_id = fields.Many2one('purchase.order', string='Purchase Order')
    revision_id = fields.Many2one('purchase.order.revision', string='Revision Group')
    next_code = fields.Integer(string='Next Code')
    reason = fields.Char(string="Reason", required=True)

    def create_revision(self):
        sale_orders = self.env['purchase.order'].search([('revision_id', '=', self.revision_id.id)])
        for rec in sale_orders:
            rec.is_completed = False
        vals = {
            'name': self.revision_id.name + '-' + ' R' + str(self.next_code),
            'state': 'draft',
            'revision_id': self.revision_id.id,
            'is_completed': True
        }
        copy_id = self.order_id.copy(default=vals)
        self.revision_id.write({
            'last_code': self.next_code
        })
        self.order_id.message_post(body=_("Revision: %s Reason: %s") % (self.next_code, self.reason))
        # self.order_id.write({
        #     'is_completed': False
        # })

        action = self.env.ref('purchase.purchase_rfq').read()[0]
        form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
        action['views'] = form_view
        action['res_id'] = copy_id.id
        return action

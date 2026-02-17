#    Stranbys Info Solution. Ltd.
#    ===========================
#    Copyright (C) 2022-TODAY Stranbys Stranbys Info Solution(<https://www.stranbys.com>)
#    Author: Stranbys Info Solution(<https://www.stranbys.com>)
from odoo import fields, models, _


class SalesRevision(models.TransientModel):
    _name = 'sale.order.revision.wizard'

    order_id = fields.Many2one('sale.order', string='Sale Order')
    revision_id = fields.Many2one('sale.order.revision', string='Revision Group')
    next_code = fields.Integer(string='Next Code')
    reason = fields.Char(string="Reason", required=True)

    def create_revision(self):
        sale_orders = self.env['sale.order'].search([('revision_id', '=', self.revision_id.id)])
        for rec in sale_orders:
            rec.is_completed = False
        # if not self.revision_id:
        name = self.order_id.name
        parts = name.split(" - ")

        if len(parts) == 2:
            part1, part2 = parts
            name = part1
        vals = {
            'name': name + ' - ' + f"{self.next_code:02d}",
            'state': 'draft',
            'revision_id': self.revision_id.id,
            'is_completed': True

        }
        copy_id = self.order_id.copy(default=vals)
        self.order_id.project_id.write({
            'project_sequence': name + ' - ' + f"{self.next_code:02d}",
            'seq': self.next_code
        })
        self.revision_id.write({
            'last_code': self.next_code
        })
        self.order_id.message_post(body=_("Revision: %s Reason: %s") % (self.next_code, self.reason))
        # self.order_id.write({
        #     'is_completed': False
        # })
        for rec in self.order_id.picking_ids:
            rec.action_cancel()
        self.order_id._action_cancel()

        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        form_view = [(self.env.ref('sale.view_order_form').id, 'form')]
        action['views'] = form_view
        action['res_id'] = copy_id.id
        return action

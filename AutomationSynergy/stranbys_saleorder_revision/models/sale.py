#    Stranbys Info Solution. Ltd.
#    ===========================
#    Copyright (C) 2022-TODAY Stranbys Stranbys Info Solution(<https://www.stranbys.com>)
#    Author: Stranbys Info Solution(<https://www.stranbys.com>)
from odoo import api, fields, models, _

READONLY_STATES = {
    'confirmed': [('readonly', True)]
}


class SalesRevision(models.Model):
    _inherit = 'sale.order'

    revision_id = fields.Many2one('sale.order.revision', string='Revision Group', copy=False)
    revision_number = fields.Char(string='Revision Number', copy=False)
    revision_count = fields.Integer(string='Revisions', compute='_compute_revision_count')
    is_completed = fields.Boolean(string="Completed", default=True)
    no_revision = fields.Boolean(copy=False, default=False, readonly=False)

    def _compute_revision_count(self):
        for record in self:
            record.revision_count = len(self.env['sale.order'].search([('revision_id', '=', self.revision_id.id)]))

    def create_new_version(self):
        revision_id = self.revision_id
        next_code = False
        if not revision_id:
            vals = {
                'name': self.name,
                'last_code': 0
            }
            revision_id = self.env['sale.order.revision'].create(vals)
            self.write({
                'revision_id': revision_id.id
            })
            next_code = revision_id.last_code

        else:
            project_id = self.project_id
            if project_id:
                next_code = project_id.seq


        return {
            'name': 'Create revision',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.revision.wizard',
            'target': 'new',
            'context': {'default_order_id': self.id,
                        'default_revision_id': revision_id.id,
                        'default_next_code': next_code + 1
                        }
        }

        # action = self.env.ref('stranbys_saleorder_revision.action_revision_wizard_sale_order').read()[0]
        # action['context'] = dict(
        #     self.env.context,
        #     default_order_id=self.id,
        #     default_revision_id=revision_id.id,
        #     default_next_code=revision_id.last_code + 1
        # )
        # return action

    def action_view_revisions(self):
        sale_orders = self.env['sale.order'].search([('revision_id', '=', self.revision_id.id)])

        result = self.env['ir.actions.act_window']._for_xml_id('stranbys_saleorder_revision.action_view_revised_quote')
        result['domain'] = [('id', 'in', sale_orders.ids)]
        return result

    def action_confirm(self):
        if self.revision_id:
            sale_orders = self.env['sale.order'].search([('revision_id', '=', self.revision_id.id)])
            for rec in sale_orders:
                if rec.id != self.id:
                    rec.is_completed = False
            self.is_completed = True
        return super(SalesRevision, self).action_confirm()


class SaleOrderGroup(models.Model):
    _name = 'sale.order.revision'

    name = fields.Char(string='Name', required=True)
    last_code = fields.Integer(string='Last Code')

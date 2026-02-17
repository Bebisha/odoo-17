
from odoo import api, fields, models, _

READONLY_STATES = {
    'confirmed': [('readonly', True)]
}


class PurchaseRevision(models.Model):
    _inherit = 'purchase.order'

    revision_id = fields.Many2one('purchase.order.revision', string='Revision Group', copy=False)
    revision_number = fields.Char(string='Revision Number', copy=False)
    revision_count = fields.Integer(string='Revisions', compute='_compute_revision_count')
    is_completed = fields.Boolean(string="Completed", default=True)
    no_revision = fields.Boolean(copy=False, default=False, readonly=False)

    def _compute_revision_count(self):
        for record in self:
            record.revision_count = len(self.env['purchase.order'].search([('revision_id', '=', self.revision_id.id),('id', '!=', self.id)]))

    def create_new_version(self):
        revision_id = self.revision_id
        if revision_id:
            self.write({
                'state': 'cancel'
            })

        else:
            vals = {
                'name': self.name,
                'last_code': 0
            }
            revision_id = self.env['purchase.order.revision'].create(vals)
            self.write({
                'revision_id': revision_id.id,'state': 'cancel'
            })
            next_code = revision_id.last_code
        return {
            'name': 'Create revision',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order.revision.wizard',
            'target': 'new',
            'context': {'default_order_id': self.id,
                        'default_revision_id': revision_id.id,
                        'default_next_code': revision_id.last_code + 1
                        }
        }

    def action_view_revisions(self):
        purchase_orders = self.env['purchase.order'].search([('revision_id', '=', self.revision_id.id),('id', '!=', self.id),('state', '=', 'cancel')])

        result = self.env['ir.actions.act_window']._for_xml_id('kg_purchase_revision.action_view_revised_quote')
        result['domain'] = [('id', 'in', purchase_orders.ids)]
        return result

    def action_confirm(self):
        if self.revision_id:
            purchase_orders = self.env['purchase.order'].search([('revision_id', '=', self.revision_id.id)])
            for rec in purchase_orders:
                if rec.id != self.id:
                    rec.is_completed = False
            self.is_completed = True
        return super(PurchaseRevision, self).action_confirm()


class SaleOrderGroup(models.Model):
    _name = 'purchase.order.revision'

    name = fields.Char(string='Name', required=True)
    last_code = fields.Integer(string='Last Code')

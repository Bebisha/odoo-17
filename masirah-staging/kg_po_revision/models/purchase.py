from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    revision_id = fields.Many2one('purchase.order', string="Revision Id")
    revision_count = fields.Integer("Number of revisions Generated")
    is_revision = fields.Boolean(string="Is Revision", default=False)
    is_check = fields.Boolean(string="Is Check", default=False)
    revision_no = fields.Many2many(
        'purchase.order', 'kg_rev_rel', 'kg_revision_id', 'revision_id', string="Revision No", store=True)


    def custom_create_revision(self):
        self.is_check = True
        if not self.revision_id:
            self.revision_id = self.id

        view_id = self.env.ref('purchase.purchase_order_form').id,
        values = self.copy()
        values.revision_count += 1
        values.is_check = False
        values.is_reject = False
        values.is_request = True
        values.is_pm_approve = False
        values.is_gm_approve = False
        values.is_rfq_approve = False
        values.requested_by = False
        values.verified_by = False
        values.approved_by = False

        active_id = self.env['purchase.order'].search([('id', '=', self.id)])

        for po in active_id:
            values.write({'revision_no': [(6, 0, po.ids)]})

        active_id.state = 'cancel'
        if active_id.picking_ids:
            active_id.picking_ids.filtered(lambda pic: pic.state != 'done').write({'state': 'cancel'})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_model': 'purchase.order',
            'res_id': values.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
        }


    def show_revisedline(self):
        return {
            'name': 'Revisions Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('revision_id', '=', self.revision_id.id), ('state', '=', 'cancel')],
        }




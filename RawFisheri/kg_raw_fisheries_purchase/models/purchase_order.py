from odoo import models, fields


class KGPurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    vessel_id = fields.Many2one("sponsor.sponsor", string="Vessel")
    partner_ref = fields.Char('Vessel Reference', copy=False,
                              help="Reference of the sales order or bid sent by the vendor. "
                                   "It's used to do the matching when you receive the "
                                   "products as this reference is usually written on the "
                                   "delivery order sent by your vendor.")

    def open_import_wizard(self):
        return {
            'name': 'Import Products',
            'type': 'ir.actions.act_window',
            'res_model': 'import.pol.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_po_id': self.id,
            }
        }

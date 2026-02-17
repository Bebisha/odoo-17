
from odoo import api, fields, models, _



class MaterialPurchaseRequisition(models.Model):
    _inherit = "material.purchase.requisition"

    division_id = fields.Many2one("kg.divisions", string="Division")
    vessel_id = fields.Many2one('vessel.code', string='Vessel')


class VendorEmailInherit(models.TransientModel):
    _inherit = 'vendor.rfq.mail'

    def create_po(self):
        """Extend create_po to pass vendor_code"""
        for rec in self:
            context = self._context
            rec.purchase_requistion_id = context.get('active_id')
            purchase_requisition = rec.purchase_requistion_id
            requisition_lines = rec.requisition_line_ids

            rfq = False
            alternative_rfq_ids = []

            for vendor in rec.vendor_ids:
                rfq = rec.create_rfq(
                    vendor,
                    purchase_requisition,
                    requisition_lines,
                    rec.user_id,
                    code=vendor.vendor_code ,
                    division_id=purchase_requisition.requisition_id.division_id.id if purchase_requisition.requisition_id.division_id else False
                    # ✅ added
                )
                alternative_rfq_ids.append(rfq.id)

            if rfq and rfq.id in alternative_rfq_ids:
                alternative_rfq_ids.remove(rfq.id)






class KGPurchaseRequisitions(models.Model):
    _inherit = "purchase.requisitions"

    vessel_id = fields.Many2one('vessel.code', string='Vessel')

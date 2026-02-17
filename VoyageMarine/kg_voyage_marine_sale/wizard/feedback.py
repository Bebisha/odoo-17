from markupsafe import Markup

from odoo import models, fields, api

class SaleOrderFeedbackWizard(models.TransientModel):
    _inherit = 'sale.order.cancel'

    _description = 'Collect Feedback for Canceled Quotation'

    feedback = fields.Text(string="Cancellation Feedback")


    def action_cancel(self):
        for rec in self:
            # rec.order_id.message_post(body=f"Cancelled reason : {rec.feedback}")
            body = Markup("<strong>Cancelled reason : </strong><br>%(reason)s") % {
                'reason': rec.feedback
            }
            rec.order_id.message_post(body=body)
            rec.order_id._action_cancel()



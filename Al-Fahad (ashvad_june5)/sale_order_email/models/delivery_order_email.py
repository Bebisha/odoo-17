from odoo import api, fields, models, _
from odoo.http import request


class DeliveryOrder(models.Model):
    _inherit = 'stock.picking'

    # def button_validate(self):
    #     res = super(DeliveryOrder, self).button_validate()
    #     template = self.env.ref('sale_order_email.delivery_order_template_name')
    #     base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
    #     ctx = {
    #         "customer_url": base_url,
    #     }
    #     template.with_context(ctx).send_mail(self.id, force_send=True)
    #     print(res, "rrrrrrrrrrrrrrrt")

    do_num = fields.Char(string="DO Number")
    receipt_num = fields.Char(string="Receipt Number")

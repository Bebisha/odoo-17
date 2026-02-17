from odoo import http
from odoo.http import request


class KGCustomSaleOrderPortal(http.Controller):

    @http.route(['/sale/order/<int:order_id>'], type='http', auth='public', website=True)
    def sale_order_view(self, order_id, **kwargs):
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists():
            return request.not_found()
        return request.render('kg_raw_fisheries_sale.kg_custom_sale_order_template', {
            'order': order
        })
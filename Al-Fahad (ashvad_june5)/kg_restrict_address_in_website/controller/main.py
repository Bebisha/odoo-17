from odoo import http
from odoo.http import request

class WebsiteSaleForm(http.Controller):

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        sale_order_id = request.session.get('sale_last_order_id')
        reference_number = request.session.get('reference_number')  # Get the reference number from the session
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            order.write({'ref_no': reference_number})  # Write the reference number to the sale order
            values = self._prepare_shop_payment_confirmation_values(order)
            return request.render("website_sale.confirmation", values)
        else:
            return request.redirect('/shop')
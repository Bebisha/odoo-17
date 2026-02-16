# controllers/website_sale.py
# from odoo.addons.website_sale.controllers.main import WebsiteSale as WebsiteSaleMain
# from werkzeug.exceptions import NotFound
# from odoo.addons.payment.controllers.portal import PaymentPortal
#
# from odoo import http, fields
# from odoo.http import request
#
#
# class CheckoutSkipPaymentInherit(PaymentPortal):
#
#     @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
#     def shop_payment_confirmation(self, **post):
#         sale_order_id = request.session.get('sale_last_order_id')
#         if sale_order_id:
#             order = request.env['sale.order'].sudo().browse(sale_order_id)
#             print('post,', post)
#             template = request.env.ref('website_sale_checkout_skip_payment.sale_order_action_confirm_template')
#             base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
#             base_url += '/web#id=%d&view_type=form&model=%s' % (order.id, order._name)
#             ctx = {
#                 "customer_url": base_url,
#             }
#             template.with_context(ctx).sudo().send_mail(order.id, force_send=True)
#             order.write({'client_order_ref': post['client_order_ref']})
#             order.action_confirm()
#             values = self._prepare_shop_payment_confirmation_values(order)
#
#             return request.render("website_sale.confirmation", values)
#         else:
#             return request.redirect('/shop')
#

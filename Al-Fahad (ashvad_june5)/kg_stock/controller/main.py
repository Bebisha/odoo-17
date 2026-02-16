from odoo import http
from odoo.http import request

# class WebsiteProduct(http.Controller):
#
#     @http.route('/shop', type='http', auth="user", website=True)
#     def shop(self, **kw):
#         # Get default warehouse of the logged-in user
#         default_warehouse = request.env.user.property_warehouse_id
#         # Fetch products in the default warehouse
#         products = request.env['product.template'].sudo().search([('warehouse_id', '=', default_warehouse.id)])
#         return http.request.render('kg_inventory.product_listing_template', {'products': products})

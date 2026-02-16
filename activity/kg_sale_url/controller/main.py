from odoo import http, tools, _
from odoo.http import request

class SaleOrder(http.Controller):
    @http.route(['/SaleOrder'], type='http', auth="public", website=True)
    def sale_order(self,**post):
        sale_data = request.env['sale.order'].sudo().search([])

        print('sale_data',sale_data)
        values = {
            'record' : sale_data
        }
        return request.render('kg_sale_url.temp_sale_data',values)
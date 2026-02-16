from odoo import http
from odoo.http import request

class SaleOrderController(http.Controller):
    @http.route('/sale_order/preview_pdf/<int:order_id>', type='http', auth='user')
    def get_preview_pdf(self, order_id, **kwargs):
        print("pppppppppppppppppp")
        order = request.env['sale.order'].sudo().browse(order_id)
        print(order.preview_pdf)
        if order.preview_pdf:
            return request.make_response(
                order.preview_pdf,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'inline; filename="preview.pdf"')
                ]
            )
        return request.not_found()


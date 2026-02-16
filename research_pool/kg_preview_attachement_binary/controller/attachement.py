from odoo import http
from odoo.http import request

class SaleOrderController(http.Controller):

    @http.route('/web/image/<model("sale.order"):order_id>/create_image', type='http', auth="user")
    def get_image(self, order_id, **kw):
        if order_id.create_image:
            return request.make_response(order_id.create_image, headers=[
                ('Content-Type', 'image/png'),  # Change the content type as needed
                ('Content-Disposition', 'inline; filename=image.png'),
            ])
        return request.not_found()

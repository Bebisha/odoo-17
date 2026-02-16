from odoo import http
from odoo.http import request


class FileController(http.Controller):

    @http.route('/get_file_base64/<int:file_id>', type='json', auth='user')
    def get_file_base64(self, file_id):
        file_base64 = request.env['sale.order'].get_file_base64(file_id)
        return {'file_base64': file_base64}

# -*- coding: utf-8 -*-
# from odoo import http


# class ImagePreview(http.Controller):
#     @http.route('/image_preview/image_preview', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/image_preview/image_preview/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('image_preview.listing', {
#             'root': '/image_preview/image_preview',
#             'objects': http.request.env['image_preview.image_preview'].search([]),
#         })

#     @http.route('/image_preview/image_preview/objects/<model("image_preview.image_preview"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('image_preview.object', {
#             'object': obj
#         })


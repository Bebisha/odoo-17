# -*- coding: utf-8 -*-
# from odoo import http


# class DevelopingChildCentre(http.Controller):
#     @http.route('/developing_child_centre/developing_child_centre', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/developing_child_centre/developing_child_centre/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('developing_child_centre.listing', {
#             'root': '/developing_child_centre/developing_child_centre',
#             'objects': http.request.env['developing_child_centre.developing_child_centre'].search([]),
#         })

#     @http.route('/developing_child_centre/developing_child_centre/objects/<model("developing_child_centre.developing_child_centre"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('developing_child_centre.object', {
#             'object': obj
#         })

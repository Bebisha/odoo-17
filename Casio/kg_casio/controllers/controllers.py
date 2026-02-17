# -*- coding: utf-8 -*-
# from odoo import http


# class KgCasio(http.Controller):
#     @http.route('/kg_casio/kg_casio/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kg_casio/kg_casio/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('kg_casio.listing', {
#             'root': '/kg_casio/kg_casio',
#             'objects': http.request.env['kg_casio.kg_casio'].search([]),
#         })

#     @http.route('/kg_casio/kg_casio/objects/<model("kg_casio.kg_casio"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kg_casio.object', {
#             'object': obj
#         })

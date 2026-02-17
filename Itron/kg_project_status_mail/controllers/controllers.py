# -*- coding: utf-8 -*-
# from odoo import http


# class KgProjectStatusMail(http.Controller):
#     @http.route('/kg_project_status_mail/kg_project_status_mail/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/kg_project_status_mail/kg_project_status_mail/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('kg_project_status_mail.listing', {
#             'root': '/kg_project_status_mail/kg_project_status_mail',
#             'objects': http.request.env['kg_project_status_mail.kg_project_status_mail'].search([]),
#         })

#     @http.route('/kg_project_status_mail/kg_project_status_mail/objects/<model("kg_project_status_mail.kg_project_status_mail"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('kg_project_status_mail.object', {
#             'object': obj
#         })

# -*- coding: utf-8 -*-
import base64
from odoo import models, api, fields, _, modules
# from openpyxl import load_workbook


class CustomerImport(models.TransientModel):
    _name = 'kg.customer.import'
    _description = 'Customer Import Sample File'

    def get_import_templates(self):
        with open(modules.get_module_resource('kg_casio', 'static/xls', 'customer_template.xls'),'rb') as f:
            return base64.b64encode(f.read())

    kg_binary_field = fields.Binary('Template', default=get_import_templates)
    fname = fields.Char(string="File Name", default='customer_template.xls')
    is_ok = fields.Boolean(default=False)

    def export_file(self):
        self.is_ok = True
        return {
            'name': _("Customer Import"),
            'context': {'is_ok': True,
                        'default_is_ok': True},
            'view_type': 'form',
            'res_model': 'kg.customer.import',
            'res_id': self.id,
            'id': self.id,
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


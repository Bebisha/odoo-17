# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SoWizard(models.TransientModel):
    _name = "so.wizard"
    _description = "SO Wizard"

    def _get_data(self):
        for data in self:
            context = dict(self._context or {})
            active_id = context.get('active_id', False)
            data.sale_id = active_id

    sale_id = fields.Many2one('sale.order', string="Sale Id",)
    report_type = fields.Selection([('with', 'With Header'), ('without', 'Without Header')], string='Report type',default='with')



    def print_report(self, context=None):
        self.ensure_one()
        data = {'ids': self.env.context.get('active_ids', [])}
        res = self.read()
        res = res and res[0] or {}
        data.update({'form': res})
        return self.env.ref('kg_curr_conv.so_with_logo').report_action(self, data=data)



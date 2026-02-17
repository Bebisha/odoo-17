# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PoWizard(models.TransientModel):
    _name = "po.wizard"
    _description = "PO Wizard"


    po_id = fields.Many2one('purchase.order', string="Purchase Id",)
    report_type = fields.Selection([('with', 'With Header'), ('without', 'Without Header')], string='Report type',
                                   default='with')

    def print_report(self, context=None):
        self.ensure_one()
        data = {'ids': self.env.context.get('active_ids', [])}
        res = self.read()
        res = res and res[0] or {}
        data.update({'form': res})
        return self.env.ref('kg_curr_conv.po_with_logo').report_action(self, data=data)



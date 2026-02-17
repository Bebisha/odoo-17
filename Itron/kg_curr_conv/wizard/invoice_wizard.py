# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InvoiceWizard(models.TransientModel):
    _name = "invoice.wizard"
    _description = "Invoice Wizard"

    @api.onchange('report_type')
    def _get_data(self):
        for data in self:
            context = dict(self._context or {})
            active_id = context.get('active_id', False)
            data.invoice_id = active_id

    invoice_id = fields.Many2one('account.move', string="Invoice Id",store=1)
    report_type = fields.Selection([('with', 'With Header'), ('without', 'Without Header')], string='Report type')

    def print_report(self, context=None):
        self.ensure_one()
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        data = {'ids': self.env.context.get('active_ids', [])}
        res = self.read()
        invoice_id = self.env['account.move'].search([('id', '=',active_id)])
        res = res and res[0] or {}
        data.update({'form': res})
        data.update({'invoice': invoice_id.id})
        return self.env.ref('kg_curr_conv.kg_print_invoice').report_action(self, data=data)



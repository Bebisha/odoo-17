# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class PdcPayment(models.TransientModel):

    _name = 'wiz.pdc.payment'
    _description = 'PDC Payment Wizard'

    effective_date = fields.Date(string='Effective Date')

    @api.model
    def default_get(self, fields):
        rec = super(PdcPayment, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        records = self.env[active_model].browse(active_ids)
        rec.update({'effective_date': records[0].cheque_date})
        return rec

    # @api.multi
    def proceed(self):
        for wiz in self:
            for payment in self.env['account.payment'].browse(
                self._context.get('active_ids')):
                    if payment.payment_method_code == 'pdc' and \
                    not payment.effective_date:
                        if wiz.effective_date < payment.cheque_date:
                            raise ValidationError(
                                _('You cannot clear cheque before %s' % 
                                  (payment.cheque_date)))
                        if not payment.related_journal:
                            raise ValidationError(_('Please enter Related Journal!'))
                        payment.write({'effective_date': wiz.effective_date,
                                       'cheque_clear': True})
                        account_pdc_type = payment.company_id.pdc_type
                        # account_pdc_type = self.env['res.config.settings'].search([
                        #     ('pdc_type', '=', 'manual')])
                        if account_pdc_type and account_pdc_type == 'manual':
                            moves = payment.create_move()
                            payment.write({'cheque_move_line_ids': moves})
            return True
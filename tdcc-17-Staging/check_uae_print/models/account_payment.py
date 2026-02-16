from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Account_Payment(models.Model):
    _inherit = 'account.payment'

    check_format_id = fields.Many2one('cheque.format',
                                      string="Cheque Format",
                                      compute="get_cheque_format_id")

    @api.depends('journal_id')
    def get_cheque_format_id(self):
        for each in self:
            if each.journal_id.account_checkbook_id:
               each.check_format_id = each.journal_id.account_checkbook_id.cheque_format_id.id

    # @api.multi
    def do_print_checks(self):
        us_check_layout = self[0].company_id.us_check_layout
        if us_check_layout != 'disabled':
            self.write({'state': 'sent'})
            if self._context and self.journal_id.account_checkbook_id:
#                 and self._context.get('default_next_check_number')
                if self.journal_id.account_checkbook_id.printed_page == 0:
                    next_page = self.journal_id.account_checkbook_id.start_page
                else:
                    next_page = self.journal_id.account_checkbook_id.printed_page + 1

                if next_page > self.journal_id.account_checkbook_id.pages:
                    raise UserError(_("Not enough cheque. Please define new cheque Book"))

                self.journal_id.account_checkbook_id.printed_page = next_page

                self = self.with_context(default_next_check_number=next_page)

            return self.env.ref('check_uae_print.action_print_uae_cheque').report_action(self)
        return super(Account_Payment, self).do_print_checks()

    # @api.multi
    def print_checks(self):
        """ Override to allow check printing for PDC as well """
        res = {}
        self = self.filtered(lambda
                                 r: r.payment_method_id.code in ('check_printing', 'pdc') and r.state != 'reconciled')

        if len(self) == 0:
            raise UserError(_(
                "Payments to print as a checks must have 'Check' selected as payment method and "
                "not have already been reconciled"))
        if any(payment.journal_id != self[0].journal_id for payment in self):
            raise UserError(_(
                "In order to print multiple checks at once, they must belong to the same bank journal."))

        if not self[0].journal_id.check_manual_sequencing:
            # The wizard asks for the number printed on the first pre-printed check
            # so payments are attributed the number of the check the'll be printed on.
            last_printed_check = self.search([
                ('journal_id', '=', self[0].journal_id.id),
                ('check_number', '!=', 0)], order="check_number desc", limit=1)
            next_check_number = last_printed_check and int(last_printed_check.check_number) + 1 or 1
            res = {
                'name': _('Print Pre-numbered Checks'),
                'type': 'ir.actions.act_window',
                'res_model': 'print.prenumbered.checks',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'payment_ids': self.ids,
                    'default_next_check_number': next_check_number,
                }
            }
        else:
            self.filtered(lambda r: r.state == 'draft').post()
            res = self.do_print_checks()
        # set 'next check number' based on specific checkbook/journal
        if res.get('context') and res.get('context').get('default_next_check_number') and self.journal_id.account_checkbook_id:

            if self.journal_id.account_checkbook_id.printed_page == 0:
                next_page = self.journal_id.account_checkbook_id.start_page
            else:
                next_page = self.journal_id.account_checkbook_id.printed_page + 1
            if next_page > self.journal_id.account_checkbook_id.pages:
                raise UserError(_("Not enough cheque. Please define new cheque Book"))

            # self.journal_id.account_checkbook_id.printed_page = next_page
            res['context'].update({'default_next_check_number': next_page})
        return res

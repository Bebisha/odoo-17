##############################################################################
#
#  Bista Solutions Inc.
#  Website: https://www.bistasolutions.com
#
##############################################################################

from odoo import models, api, _
from odoo.tools import append_content_to_html
from odoo.exceptions import UserError
import base64


class AccountFollowupReport(models.AbstractModel):
    _inherit = 'account.followup.report'

    ''' Method override and Partner Due invoice Pdf attached in mail'''

    @api.model
    def send_email(self, options):
        """
        Send by mail the followup to the customer
        """
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        email = self.env['res.partner'].browse(partner.address_get(
            ['invoice'])['invoice']).email
        options['keep_summary'] = True
        if email and email.strip():
            body_html = self.with_context(print_mode=True, mail=True,
                                          lang=partner.lang or
                                          self.env.user.lang).get_html(
                                              options)
            start_index = body_html.find(b'<span>', body_html.find(
                b'<div class="o_account_reports_summary">'))
            end_index = start_index > -1 and body_html.find(
                b'</span>', start_index) or -1
            if end_index > -1:
                replaced_msg = body_html[start_index:end_index].replace(
                    b'\n', b'<br />')
                body_html = body_html[:start_index] + replaced_msg + body_html[
                    end_index:]
            msg = _('Follow-up email sent to %s') % email
            msg += '<br>' + body_html.decode('utf-8')
            msg_id = partner.message_post(body=msg)
            res = {}
            invoice_id = self.env['account.move']
            attachment_obj = self.env['ir.attachment']
            attachment_lst = []
            for l in partner.unreconciled_aml_ids:
                if l.company_id == self.env.user.company_id:
                    if l.blocked:
                        continue
                    currency = l.currency_id or l.company_id.currency_id
                    if currency not in res:
                        res[currency] = []
                    res[currency].append(l)
            for currency, aml_recs in res.items():
                for aml in aml_recs:
                    invoice_id |= aml.invoice_id
            invoice_action = self.env.ref('account.account_invoices')
            for inv in invoice_id:
                pdf = invoice_action.render_qweb_pdf(inv.id)
                b64_pdf = base64.b64encode(pdf[0])
                attachment_id = attachment_obj.create({
                    'name': inv.number,
                    'type': 'binary',
                    'datas': b64_pdf,
                    'datas_fname': inv.number + '.pdf',
                    'store_fname': inv.number,
                    'res_model': 'account.move',
                    'res_id': inv.id,
                    'mimetype': 'application/x-pdf'
                })
                attachment_lst.append(attachment_id.id)
            email = self.env['mail.mail'].create({
                'mail_message_id': msg_id.id,
                'subject': _('%s Payment Reminder') % (
                    self.env.user.company_id.name) + ' - ' + partner.name,
                'body_html': append_content_to_html(
                    body_html, self.env.user.signature or '', plaintext=False),
                'email_from': self.env.user.email or '',
                'email_to': email,
                'body': msg,
                'attachment_ids': [(6, 0, attachment_lst)],
            })
            partner.message_subscribe([partner.id])
            return True
        raise UserError(_('Could not send mail to partner because it'
                          'does not have any email address defined'))

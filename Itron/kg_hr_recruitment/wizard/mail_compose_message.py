# -*- coding: utf-8 -*-
from odoo import fields, models, api


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    email_to = fields.Text('To', help='Message recipients (emails)')
    email_cc_ids = fields.Many2many('hr.employee', string='Email cc', copy=False)

    @api.depends('composition_mode', 'email_from', 'model',
                 'res_domain', 'res_ids', 'template_id')
    def _compute_authorship(self):
        """ Computation is coming either from template, either from context.
        When having a template with a value set, copy it (in batch mode) or
        render it (in monorecord comment mode) on the composer. Otherwise
        try to take current user's email. When removing the template, fallback
        on default thread behavior (which is current user's email).

        Author is not controllable from the template currently. We therefore
        try to synchronize it with the given email_from (in rendered mode to
        avoid trying to find partner based on qweb expressions), or fallback
        on current user. """
        Thread = self.env['mail.thread'].with_context(active_test=False)
        for composer in self:
            rendering_mode = composer.composition_mode == 'comment' and not composer.composition_batch
            updated_author_id = None
            active_model = self.env.context.get('active_model')
            if active_model == 'hr.applicant' and len(self.env.context.get('active_ids', [])) <= 1:
                outgoing_mail_server = self.env['ir.mail_server'].search([], limit=1)
                email_from = outgoing_mail_server.smtp_user
                composer.email_from = email_from
                updated_author_id = self.env.user.partner_id.id
            else:
                # update email_from first as it is the main used field currently
                if composer.template_id.email_from:
                    composer._set_value_from_template('email_from')
                # removing template or void from -> fallback on current user as default
                elif not composer.template_id or not composer.email_from:
                    composer.email_from = self.env.user.email_formatted
                    updated_author_id = self.env.user.partner_id.id

            # Update author. When being in rendered mode: link with rendered
            # email_from or fallback on current user if email does not match.
            # When changing template in raw mode or resetting also fallback.
            if composer.email_from and rendering_mode and not updated_author_id:
                updated_author_id, _ = Thread._message_compute_author(
                    None, composer.email_from, raise_on_email=False,
                )
                if not updated_author_id:
                    updated_author_id = self.env.user.partner_id.id
            if not rendering_mode or not composer.template_id:
                updated_author_id = self.env.user.partner_id.id

            if updated_author_id:
                composer.author_id = updated_author_id

    def action_send_mail(self):
        """Override function to include email CC and email TO fields."""
        active_model = self.env.context.get('active_model')
        if active_model == 'hr.applicant' and len(self.env.context.get('active_ids', [])) <= 1:
            cc_emails = ','.join(partner.work_email for partner in self.email_cc_ids if partner.work_email)
            email_to = self.email_to or ''
            return self.with_context(email_cc=cc_emails, email_to=email_to)._action_send_mail()
        return super().action_send_mail()

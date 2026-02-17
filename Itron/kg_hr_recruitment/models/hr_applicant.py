# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from num2words import num2words
import base64


class HRApplicant(models.Model):
    _inherit = "hr.applicant"

    sequence = fields.Char('Ref NO', required="True", default=lambda self: _('New'), readonly=True, copy=False)
    current_salary = fields.Float("Current Salary", group_operator="avg", help="Current Salary by Applicant",
                                  tracking=True, groups="hr_recruitment.group_hr_recruitment_user")
    applicant_notice_period = fields.Char("Notice Period",
                                          help="The notice period the applicant is serving at their current or previous company.",
                                          tracking=True, groups="hr_recruitment.group_hr_recruitment_user")
    communication_skill_mark = fields.Float('Communication',
                                            help="Communication skill Mark by Applicant")
    attitude_skill_mark = fields.Float('Attitude', help="Attitude Skill Mark by Applicant")
    aptitude_skill_mark = fields.Float('Aptitude', help="Aptitude skill Mark by Applicant")
    commitment_mark = fields.Float('Commitment', help="Commitment Mark by Applicant")

    first_level_total = fields.Float('Total',
                                     help="Total marks obtained by the applicant in the first-level interview",
                                     compute='_compute_total_mark_all_level')
    first_level_total_in_percent = fields.Float('Total In Percentage',
                                                help="Total marks obtained in Percentage by the applicant in the first-level interview",
                                                compute='_compute_total_mark_all_level')

    technical_first_level_skill = fields.Float('Technical First Level',
                                               help="Technical First Level Skill Mark by Applicant")
    technical_first_level_total = fields.Float('Total',
                                               help="Technical First Level Total Mark by Applicant",
                                               compute='_compute_total_mark_all_level')
    technical_second_level_skill = fields.Float('Technical Second Level',
                                                help="Technical Second Level Skill Mark by Applicant")
    technical_second_level_total = fields.Float('Total',
                                                help="Technical Second Level Total Mark by Applicant",
                                                compute='_compute_total_mark_all_level')
    hr_round_skill = fields.Float('HR',
                                  help="HR Round Skill Mark by Applicant")
    hr_round_total = fields.Float('Total',
                                  help="HR Round Total Mark by Applicant", compute='_compute_total_mark_all_level')
    total_mark = fields.Float('Total Mark', help="Total marks obtained by the applicant in the interview",
                              compute='_compute_total_mark')
    applicant_remark = fields.Html('Remark')
    reporting_to = fields.Char('Reporting To', copy=False)
    offer_letter_date = fields.Date('Offer Letter Date', copy=False)
    applicant_start_date = fields.Date('Applicant Start Date', copy=False)
    amount_in_words = fields.Char('Amount In Words', compute='compute_amount_in_words')
    applicant_aadhar_no = fields.Char('Aadhar NO', copy=False)
    # address fields
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email_to_cc_ids = fields.Many2many('hr.employee', string='Email cc', copy=False)
    is_proposal = fields.Boolean(string='Is HR', readonly=True, related='stage_id.is_proposal')
    roles = fields.Html('Roles and Responsibilities', copy=False, related='job_id.job_rules')
    basic_salary = fields.Float('Basic', copy=False)
    hra = fields.Float('HRA', copy=False)
    allowances = fields.Float('Allowances', copy=False)
    utility_expenses_allowance = fields.Float('Utility Expenses Allowance', copy=False)
    telephone_allowance = fields.Float('Telephone Allowance', copy=False)
    salary_total = fields.Float('Total', copy=False, compute='_compute_salary_total_of_applicant')
    applicant_passport_no = fields.Char('Passport NO', copy=False)
    office_email = fields.Char('Office Email', copy=False)
    office_phone = fields.Char('Office Phone', copy=False)
    office_location = fields.Char('Office Location', copy=False)
    country_code = fields.Char('Country Code', related='company_id.country_code', readonly=True, copy=False)
    pick_offer_letter = fields.Binary('Upload Offer Letter', copy=False)

    # additional fields for applicant
    application_date = fields.Date('Application Date', copy=False)
    total_exp = fields.Float('Total Experience', copy=False)
    r_exp = fields.Float('Relevant Experience', copy=False)
    current_designation = fields.Char('Current Designation', copy=False)
    percent_for_hike = fields.Float('Hike Percentage', copy=False, compute="compute_hike_percentage_applicant")
    reason_job_change = fields.Char('Reason For Job Change', copy=False)
    marital_status = fields.Selection(
        [('single', 'Single'), ('married', 'Married'), ('other', 'Other')], default="single", string='Marital Status')
    current_location_applicant = fields.Char('Current Location', copy=False)
    source = fields.Char('Source', copy=False)
    current_company = fields.Char('Current Company', copy=False)
    send_email = fields.Boolean(default=False)

    @api.model
    def create(self, vals):
        """ Add HR Applicant reference number with yearly reset """
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].with_context(ir_sequence_date_range="%s-01-01").next_by_code(
                'hr.applicant') or _('New')
        res = super(HRApplicant, self).create(vals)
        return res

    @api.model
    def write(self, vals):
        result = super(HRApplicant, self).write(vals)
        return result

    @api.onchange('communication_skill_mark', 'attitude_skill_mark', 'aptitude_skill_mark', 'commitment_mark',
                  'technical_first_level_skill', 'technical_second_level_skill', 'hr_round_skill',
                  )
    def onchange_check_validation(self):
        """Onchange function to validate that the above field value does not exceed 10."""
        for record in self:
            if record.communication_skill_mark > 10:
                raise ValidationError(
                    "The Communication Skill mark cannot be greater than 10. Please enter a value within the range."
                )
            if record.attitude_skill_mark > 10:
                raise ValidationError(
                    "The Attitude Skill mark cannot be greater than 10. Please enter a value within the range."
                )
            if record.aptitude_skill_mark > 10:
                raise ValidationError(
                    "The Aptitude mark cannot be greater than 10. Please enter a value within the range."
                )
            if record.commitment_mark > 10:
                raise ValidationError(
                    "The Commitment mark cannot be greater than 10. Please enter a value within the range."
                )
            if record.technical_first_level_skill > 10:
                raise ValidationError(
                    "The Technical First Level Skill mark cannot be greater than 10. Please enter a value within the range."
                )
            if record.technical_second_level_skill > 10:
                raise ValidationError(
                    "The Technical Second Level Skill mark cannot be greater than 10. Please enter a value within the range."
                )
            if record.hr_round_skill > 10:
                raise ValidationError(
                    "The HR Round Skill mark cannot be greater than 10. Please enter a value within the range."
                )

    @api.depends('communication_skill_mark', 'attitude_skill_mark', 'aptitude_skill_mark', 'commitment_mark',
                 'technical_first_level_skill', 'technical_second_level_skill', 'hr_round_skill',
                 )
    def _compute_total_mark_all_level(self):
        """ Compute the total marks for the first-level interview. """
        for record in self:
            total_mark = (
                    record.communication_skill_mark +
                    record.attitude_skill_mark +
                    record.aptitude_skill_mark + record.commitment_mark
            )
            record.first_level_total = (total_mark / 40) * 10 if total_mark > 0 else 0

            record.first_level_total_in_percent = (total_mark / 40) * 10 / 10 if total_mark > 0 else 0

            record.technical_first_level_total = (
                                                         record.technical_first_level_skill / 10) * 20 / 10 if record.technical_first_level_skill else 0
            record.technical_second_level_total = (
                                                          record.technical_second_level_skill / 10) * 40 / 10 if record.technical_second_level_skill else 0
            record.hr_round_total = (
                                            record.hr_round_skill / 10) * 30 / 10 if record.hr_round_skill else 0

    @api.depends('first_level_total_in_percent', 'technical_first_level_total', 'technical_second_level_total',
                 'hr_round_total')
    def _compute_total_mark(self):
        """ Compute the total marks obtained by the applicant. """
        for record in self:
            total = sum(
                [record.first_level_total_in_percent, record.technical_first_level_total,
                 record.technical_second_level_total,
                 record.hr_round_total])
            record.total_mark = total

    @api.depends('salary_proposed')
    def compute_amount_in_words(self):
        """ Compute the amount in words based on the Proposed Salary."""
        for record in self:
            if record.salary_proposed and isinstance(record.salary_proposed, (int, float)):
                record.amount_in_words = (
                        num2words(record.salary_proposed, lang='en').capitalize() + " only"
                )
            else:
                record.amount_in_words = ''

    def action_send_offer_letter(self):
        """Button action to print the contract including the salary details."""
        self.ensure_one()
        pdf_offer_letter = None
        if self.company_id.country_code == 'IN':
            pdf_offer_letter = self.env['ir.actions.report']._render_qweb_pdf(
                'kg_hr_recruitment.action_offer_letter_id', res_ids=self.ids)
        elif self.company_id.country_code in ['AE', 'OM', 'BH', 'US']:
            pdf_offer_letter = self.env['ir.actions.report']._render_qweb_pdf(
                'kg_hr_recruitment.action_ae_offer_letter_id', res_ids=self.ids)
        b64_pdf = base64.b64encode(pdf_offer_letter[0])
        name = "Provisional Offer Letter"
        offer_letter_pdf = self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        msg = '<p>Dear,</p>\n\n'
        msg += self.partner_name + "<br/>" + "<br/>"
        msg += 'Here is in attachment a Offer Letter of ' + '<strong>{}</strong>'.format(
            self.partner_name) + ' from ' + (
                   self.company_id.name) + '.' + '<br/>' + '<br/>'
        msg += 'If you have any questions, please do not hesitate to contact us.' + '<br/>' + '<br/>' + 'Best regards,'
        load_template = self.env['mail.template'].create({
            'name': 'Offer Letter Attachment',
            'auto_delete': True,
            'subject': "Provisional Offer Letter",
            'body_html': msg,
            'model_id': self.env.ref('hr_recruitment.model_hr_applicant').id,
        })
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_offer_letter', False):
                template_id = ir_model_data._xmlid_lookup('hr_recruitment.hr_applicant_view_form')[1]
            else:
                template_id = ir_model_data._xmlid_lookup('hr_recruitment.hr_applicant_view_form')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'hr.applicant',
            'active_model': 'hr.applicant',
            'active_id': self.ids[0],
            'default_res_ids': [self.ids[0]],
            'default_use_template': bool(template_id),
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
            'mark_rfq_as_sent': False,
            'default_attachment_ids': [fields.Command.link(offer_letter_pdf.ids)],
            'default_partner_ids': self.partner_id.ids,
            'default_template_id': load_template.id,
            'default_email_to': self.email_from,
            'default_email_cc_ids': [fields.Command.link(cc_id) for cc_id in self.email_to_cc_ids.ids],
        })
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id', 'default_attachment_ids'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id'][0]])[ctx['default_res_id'][0]]
        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Application') if self else False
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_final_offer_letter(self):
        """ Button action to print the Detailed offer letter of the applicant."""
        self.ensure_one()
        pdf_offer_letter = None
        if self.company_id.country_code == 'IN':
            pdf_offer_letter = self.env['ir.actions.report']._render_qweb_pdf(
                'kg_hr_recruitment.action_final_offer_letter_id', res_ids=self.ids)
        elif self.company_id.country_code in ['AE', 'OM', 'BH', 'US']:
            pdf_offer_letter = self.env['ir.actions.report']._render_qweb_pdf(
                'kg_hr_recruitment.action_final_ae_offer_letter_id', res_ids=self.ids)
        b64_pdf = base64.b64encode(pdf_offer_letter[0])
        name = "Detailed Offer Letter"
        offer_letter_pdf = self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        msg = '<p>Dear,</p>\n\n'
        msg += self.partner_name + "<br/>" + "<br/>"
        msg += 'Here is in attachment a Offer Letter of ' + '<strong>{}</strong>'.format(
            self.partner_name) + ' from ' + (
                   self.company_id.name) + '.' + '<br/>' + '<br/>'
        msg += 'If you have any questions, please do not hesitate to contact us.' + '<br/>' + '<br/>' + 'Best regards,'
        load_template = self.env['mail.template'].create({
            'name': 'Detailed Offer Letter Attachment',
            'auto_delete': True,
            'subject': "Detailed Offer Letter",
            'body_html': msg,
            'model_id': self.env.ref('hr_recruitment.model_hr_applicant').id,
        })
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_offer_letter', False):
                template_id = ir_model_data._xmlid_lookup('hr_recruitment.hr_applicant_view_form')[1]
            else:
                template_id = ir_model_data._xmlid_lookup('hr_recruitment.hr_applicant_view_form')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'hr.applicant',
            'active_model': 'hr.applicant',
            'active_id': self.ids[0],
            'default_res_ids': [self.ids[0]],
            'default_use_template': bool(template_id),
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
            'mark_rfq_as_sent': False,
            'default_attachment_ids': [fields.Command.link(offer_letter_pdf.ids)],
            'default_partner_ids': self.partner_id.ids,
            'default_template_id': load_template.id,
            'default_email_to': self.email_from,
            'default_email_cc_ids': [fields.Command.link(cc_id) for cc_id in self.email_to_cc_ids.ids],
        })
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id', 'default_attachment_ids'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id'][0]])[ctx['default_res_id'][0]]
        self = self.with_context(lang=lang)
        ctx['model_description'] = _('Application') if self else False
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.depends('basic_salary', 'hra', 'allowances')
    def _compute_salary_total_of_applicant(self):
        """ Compute the total salary of the employee by summing basic salary, HRA, and allowances. """
        for rec in self:
            rec.salary_total = (rec.basic_salary or 0) + (rec.hra or 0) + (rec.allowances or 0) + (
                    rec.utility_expenses_allowance or 0) + (rec.telephone_allowance or 0)

    @api.depends('current_salary', 'salary_expected')
    def compute_hike_percentage_applicant(self):
        """Compute the percentage of an applicant's salary hike."""
        for applicant in self:
            if applicant.current_salary > 0:
                applicant.percent_for_hike = ((
                                                      applicant.salary_expected - applicant.current_salary) / applicant.current_salary) * 1
            else:
                applicant.percent_for_hike = 0.0

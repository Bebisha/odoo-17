# -*- coding: utf-8 -*-
from datetime import date, timedelta
from odoo import models, fields, api, _


class HrEmployeeDocument(models.Model):
    _name = 'hr.employee.document'
    _description = 'HR Employee Documents'

    def mail_reminder(self):
        """Sending document expiry notification to employees."""

        date_now = fields.Date.today()
        match = self.search([])
        emails = []
        for user in self.env.company.hr_expiry_manager_ids:
            if user.partner_id and user.partner_id.email:
                emails.append(user.partner_id.email)
        for i in match:
            if i.expiry_date:
                if i.notification_type == 'single':
                    if i.employee_ref:
                        if date_now == i.expiry_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+" is going to expire on " + \
                                           str(i.expiry_date) + ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.partner_id:
                        if date_now == i.expiry_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+" is going to expire on " + \
                                           str(i.expiry_date) + ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.company_id:
                        if date_now == i.expiry_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+" is going to expire on " + \
                                           str(i.expiry_date) + ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': i.company_id.email,
                            }
                            self.env['mail.mail'].create(main_content).send()

                elif i.notification_type == 'multi':
                    if i.employee_ref:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) - timedelta(days=i.before_days)
                        if date_now == exp_date or date_now == i.expiry_date:  # on Expire date and few days(As it set) before expire date
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+"  is going to expire on " + str(
                                i.expiry_date) + \
                                           ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.partner_id:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) - timedelta(days=i.before_days)
                        if date_now == exp_date or date_now == i.expiry_date:  # on Expire date and few days(As it set) before expire date
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+" is going to expire on " + str(
                                i.expiry_date) + \
                                           ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.company_id:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) - timedelta(days=i.before_days)
                        if date_now == exp_date or date_now == i.expiry_date:  # on Expire date and few days(As it set) before expire date
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+"  is going to expire on " + str(
                                i.expiry_date) + \
                                           ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()


                elif i.notification_type == 'everyday':
                    if i.employee_ref:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) - timedelta(days=i.before_days)
                        if date_now >= exp_date or date_now == i.expiry_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+" is going to expire on " + str(
                                i.expiry_date) + \
                                           ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': i.emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.partner_id:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) - timedelta(days=i.before_days)
                        if date_now >= exp_date or date_now == i.expiry_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+"  is going to expire on " + str(
                                i.expiry_date) + \
                                           ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.company_id:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) - timedelta(days=i.before_days)
                        if date_now >= exp_date or date_now == i.expiry_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+" is going to expire on " + str(
                                i.expiry_date) + \
                                           ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                elif i.notification_type == 'everyday_after':
                    if i.employee_ref:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) + timedelta(days=i.before_days)
                        if date_now <= exp_date or date_now == i.expiry_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+"  is expired on " + str(i.expiry_date) + \
                                           ". Please renew it "
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.partner_id:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) + timedelta(days=i.before_days)
                        if date_now <= exp_date or date_now == i.expiry_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+"  is expired on " + str(i.expiry_date) + \
                                           ". Please renew it "
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.company_id:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) + timedelta(days=i.before_days)
                        if date_now <= exp_date or date_now == i.expiry_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+"  is expired on " + str(i.expiry_date) + \
                                           ". Please renew it "
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                else:
                    if i.employee_ref:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) - timedelta(days=7)
                        if date_now == exp_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+"  is going to expire on " + \
                                           str(i.expiry_date) + ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.partner_id:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) - timedelta(days=7)
                        if date_now == exp_date:
                            mail_content = "Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+"  is going to expire on " + \
                                           str(i.expiry_date) + ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

                    if i.company_id:
                        exp_date = fields.Date.from_string(
                            i.expiry_date) - timedelta(days=7)
                        if date_now == exp_date:
                            mail_content ="Dear Team" + ",<br>The Document " + i.name + " of "+ i.employee_ref.name+"  is going to expire on " + \
                                           str(i.expiry_date) + ". Please renew it before expiry date"
                            main_content = {
                                'subject': _('Document-%s Expired On %s') % (
                                    i.name, i.expiry_date),
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': emails,
                            }
                            self.env['mail.mail'].create(main_content).send()

    @api.constrains('expiry_date')
    def check_expr_date(self):
        for each in self:
            if each.expiry_date:
                exp_date = fields.Date.from_string(each.expiry_date)
                if exp_date < date.today():
                    raise Warning('Your Document Is Expired.')

    name = fields.Char(string='Document Number', required=True, copy=False,
                       help='You can give your'
                            'Document number.')
    description = fields.Text(string='Description', copy=False,
                              help="Description")
    expiry_date = fields.Date(string='Expiry Date', copy=False,
                              help="Date of expiry")

    employee_ref = fields.Many2one('hr.employee', copy=False)
    partner_id = fields.Many2one('res.partner', copy=False)
    company_id = fields.Many2one('res.company', copy=False)

    is_employee = fields.Boolean(default=False, copy=False, string="Is Employee")
    is_partner = fields.Boolean(default=False, copy=False, string="Is Partner")
    is_company = fields.Boolean(default=False, copy=False, string="Is Company")

    doc_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_rel',
                                         'doc_id', 'attach_id3',
                                         string="Attachment",
                                         help='You can attach the copy of your document',
                                         copy=False)
    issue_date = fields.Date(string='Issue Date', default=fields.datetime.now(),
                             help="Date of issue", copy=False)
    document_type = fields.Many2one('document.type', string="Document Type",
                                    help="Document type")
    before_days = fields.Integer(string="Days",
                                 help="How many number of days before to get the notification email")
    notification_type = fields.Selection([
        ('single', 'Notification on expiry date'),
        ('multi', 'Notification before few days'),
        ('everyday', 'Everyday till expiry date'),
        ('everyday_after', 'Notification on and after expiry')
    ], string='Notification Type',
        help="""
        Notification on expiry date: You will get notification only on expiry date.
        Notification before few days: You will get notification in 2 days.On expiry date and number of days before date.
        Everyday till expiry date: You will get notification from number of days till the expiry date of the document.
        Notification on and after expiry: You will get notification on the expiry date and continues upto Days.
        If you did't select any then you will get notification before 7 days of document expiry.""")

    @api.onchange('employee_ref')
    def remove_unwanted_values_1(self):
        for rec in self:
            if rec.employee_ref:
                rec.partner_id = False
                rec.company_id = False
                rec.is_employee = True

    @api.onchange('partner_id')
    def remove_unwanted_values_2(self):
        for rec in self:
            if rec.partner_id:
                rec.employee_ref = False
                rec.company_id = False
                rec.is_partner = True

    @api.onchange('company_id')
    def remove_unwanted_values_3(self):
        for rec in self:
            if rec.company_id:
                rec.employee_ref = False
                rec.partner_id = False
                rec.is_company = True


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    document_count = fields.Integer(compute='compute_document_count',
                                    string='# Documents')

    def compute_document_count(self):
        for each in self:
            document_ids = self.env['hr.employee.document'].sudo().search(
                [('employee_ref', '=', each.id)])
            each.document_count = len(document_ids)

    def document_view(self):
        self.ensure_one()
        domain = [
            ('employee_ref', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'hr.employee.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="oe_view_nocontent_create">
                             Click to Create for New Documents
                          </p>'''),
            'limit': 80,
            'context': "{'default_employee_ref': %s}" % self.id
        }


class HrEmployeeAttachment(models.Model):
    _inherit = 'ir.attachment'

    doc_attach_rel = fields.Many2many('hr.employee.document',
                                      'doc_attachment_id', 'attach_id3',
                                      'doc_id',
                                      string="Attachment", invisible=1)
    attach_rel = fields.Many2many('hr.document', 'attach_id', 'attachment_id3',
                                  'document_id',
                                  string="Attachment", invisible=1)

# -*- coding: utf-8 -*-
import calendar
from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, tools, _, api, Command
from odoo.exceptions import ValidationError


class ProjectContractRequest(models.Model):
    _name = 'project.contract.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Model for Contract Request"

    name = fields.Char('Name', default=lambda self: _('New'), copy=False, )
    contract_type = fields.Selection([('onsite', 'Onsite'), ('offshore', 'Offshore')], 'Contract Type',
                                     default='onsite')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)

    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    po_no = fields.Char('Contract Number', copy=False, readonly=True, index=True, default=lambda self: _(''))

    date_sign = fields.Date('Sign Date', copy=False)
    date_contract = fields.Date('Contract Date', copy=False)
    date_start = fields.Date('Start Date', default=fields.Date.context_today, copy=False)
    date_end = fields.Date('End Date')
    project_id = fields.Many2one('project.project', 'Project')
    engagement_id = fields.Many2one('project.engagement', 'Contract Period')
    recurring_id = fields.Many2one('recurrence.period', 'Recurrence Period')
    # provision_contract = fields.Selection([('subscription', 'Subscription'), ('invoice', 'Invoice')],
    #                                       default='subscription',
    #                                       string='Direct Invoice/Subscription')
    provision_contracts = fields.Selection([('subscription', 'Subscription'), ('invoice', 'Invoice')],
                                           'Direct Invoice/Subscription',
                                           default='subscription')
    parent_id = fields.Many2one('project.contract.request', copy=False)
    level1 = fields.Char('Level 1', placeholder=True)
    level2 = fields.Char('Level 2')
    level3 = fields.Char('Level 3')

    industry = fields.Char('Industry')
    terms = fields.Html(string='Terms&Conditions')
    amc_bool = fields.Boolean('AMC')
    attachments = fields.Binary('Attachment')
    attach_ids = fields.Many2many('ir.attachment',
                                  'attach_rel', 'doc_id',
                                  'attach_id3', string="Attachment",
                                  help='You can attach the copy of your'
                                       ' document.', copy=False)
    resource_id = fields.Many2many('res.users', 'resources_ids_rel', string='Resources')
    contact_count = fields.Float('Contracts', default=0, compute='compute_contracts')
    plan_id = fields.Many2one('subscription.package.plan', 'Subscription Plan')

    state = fields.Selection([
        ('draft', 'Hold'),
        ('send', 'Request Send'),
        ('sign', 'Signed'),
        ('approve', 'Active'),
        ('complete', 'Completed'),
        ('reject', 'Canceled'),
        ('expire', 'Expired'),
        ('invoice', 'Invoiced'),
        ('paid',"Paid"),
        ('partial', "Partially Paid"),
        ('subscription', 'Subscription Created'),
    ], string='Status', default='draft', tracking=True)
    total_amount = fields.Float(string="Total Amount", required=True)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    invoice_id = fields.Many2one('account.move', string='Invoice', )
    subscription_id = fields.Many2one('subscription.package', string='Subscription',copy=False )
    context_state = fields.Char(compute='_compute_context_state', store=False)
    allowed_company_ids = fields.Many2many('res.company',string='Visible Companies', default=lambda self: self.env.company.ids)


    @api.depends('contract_type')
    def _compute_context_state(self):
        for record in self:
            record.context_state = 'onsite' if record.contract_type == 'onsite' else 'offshore'

    def compute_contracts(self):
        for record in self:
            record.contact_count = self.env['project.contract.request'].search_count(
                [('parent_id', '=', self.id)])

    def complete_button(self):
        """Complete Button"""
        self.write({
            'state': 'complete'
        })

    def cron_action_to_expire(self):
        """cron action to expire expired contracts"""
        print("revathyyyyyyyyyyyy")
        today = fields.Date.today()
        for rec in self.search([]):
            if rec.date_end and rec.date_end <= today:
                rec.write({
                    'state': 'expire'
                })

    @api.model_create_multi
    def create(self, vals_list):
        """ Create a sequence for the contract request model """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('contract.reference')
                vals['name'] = sequence
            if vals.get('po_no', _('')) == _(''):
                if vals.get('contract_type') == 'onsite':
                    sequence = self.env['ir.sequence'].next_by_code('contract.number.onsite')
                elif vals.get('contract_type') == 'offshore':
                    sequence = self.env['ir.sequence'].next_by_code('contract.number.offshore')
                else:
                    sequence = _('')
                vals['po_no'] = sequence
        return super().create(vals_list)

    def action_contract_end_date_over(self):
        """Action for scheduling an action for ending date"""
        current_date = date.today()
        target_date = current_date + timedelta(days=2)  # Calculate the target date, two days from today

        contracts_ending = self.search([
            ('date_end', '=', target_date), ('state', 'not in', ('draft', 'cancel'))
        ])

        if contracts_ending:
            for contract in contracts_ending:
                data_config = self.env['res.config.settings'].sudo().search([])
                group_send_mail = []

                for config_rec in data_config.contract_approval_ids:
                    if config_rec.email:
                        group_send_mail.append(config_rec.email)

                subject = _('Contract Is Expiring')
                body = _('Contract is expiring in two days for customer "%s".') % (
                    contract.partner_id.name)

                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': ', '.join(group_send_mail),
                }
                self.env['mail.mail'].create(mail_values).send()

    def create_subscription(self):
        if self.plan_id:
            product_id = False
            if self.contract_type == 'onsite':
                product_id = self.env.ref('kg_contracts.product_product_onsite_subscription_')
            elif self.contract_type == 'offshore':
                product_id = self.env.ref('kg_contracts.product_product_offshore_subscription_')

            if product_id:
                product = self.env['product.product'].browse(product_id.id)
                subscription = self.env['subscription.package'].sudo().create({
                    'partner_id': self.partner_id.id,
                    'start_date': self.date_start,
                    'currency_id': self.currency_id.id,
                    'reference_code': False,
                    'recurrence_period_id': self.recurring_id.id,
                    'plan_id': self.plan_id.id,
                    'contract_id': self.id,
                    'product_line_ids': [
                        (0, 0, {
                            'product_id': product.id if product else False,
                            'product_qty': 1,
                        })]
                })
                subscription_list = subscription
                subscription_id = subscription_list[0].id
                self.write({'state': 'subscription', 'subscription_id': subscription_id})

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Subscriptions',
                    'res_model': 'subscription.package',
                    'res_id': self.subscription_id.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'current',
                }
        else:
            raise ValidationError('Choose a Subscription plan')

    def view_subs(self):
        self.ensure_one()
        if not self.subscription_id:
            raise ValidationError("No subscription linked to this record.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subscriptions',
            'res_model': 'subscription.package',
            'res_id': self.subscription_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }

    # @api.onchange('date_start', 'engagement_id')
    # def on_change_contract(self):
    #     month = self.engagement_id.no_month
    #     confirmation_date = self.date_start + relativedelta(months=month, days=-1)
    #     self.write({
    #         "date_end": confirmation_date
    #
    #     })

    @api.onchange('date_start', 'recurring_id')
    def on_change_contract_recurrence(self):
        # if not self.date_start or not self.recurring_id:
        #     self.confirmation_date = False
        #     return

        unit = self.recurring_id.unit
        duration = self.recurring_id.duration

        if unit == 'years':
            confirmation_date = self.date_start + relativedelta(years=duration, days=-1)
        elif unit == 'days':
            confirmation_date = self.date_start + relativedelta(days=duration - 1)
        elif unit == 'months':
            confirmation_date = self.date_start + relativedelta(months=duration, days=-1)
        elif unit == 'weeks':
            confirmation_date = self.date_start + relativedelta(weeks=duration, days=-1)
        elif unit == 'hours':
            confirmation_date = self.date_start + relativedelta(hours=duration)
        else:
            confirmation_date = False
        self.write({
            "date_end": confirmation_date

        })

    @api.onchange('amc_bool')
    def on_change_amc_periode(self):
        """set contract period for Amc"""
        contract = self.env['project.engagement'].search([('no_month', '=', 12)])
        self.engagement_id = False
        if self.amc_bool:
            self.write({
                "engagement_id": contract.id

            })

    def send_mail(self):
        """Send email to approves"""
        data_config = self.env['res.config.settings'].sudo().search([])
        group_send_mail = []

        for config_rec in data_config.contract_approval_ids:
            if config_rec.email:
                group_send_mail.append(config_rec.email)

        subject = _('Contract  for : %s') % self.partner_id.name

        body = _('Contract of type "%s" has been Confirmed for customer "%s".') % (
            self.contract_type, self.partner_id.name)

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        url = "{}/web#id={}&view_type=form&model={}".format(base_url, self.id, self._name)

        link_tag = "<a href='{}'>{}</a>".format(url, "Click here to view")

        mail_values = {
            'subject': subject,
            'body_html': body + "<br/>" + link_tag,
            'email_to': ', '.join(group_send_mail),
        }
        self.env['mail.mail'].create(mail_values).send()

    def create_invoice(self):
        for contract_request in self:
            product_id = False
            if contract_request.contract_type == 'onsite':
                product_id = self.env.ref('kg_contracts.product_product_onsite').id
            elif contract_request.contract_type == 'offshore':
                product_id = self.env.ref('kg_contracts.product_product_offshore').id

            if product_id:
                product = self.env['product.product'].browse(product_id)
                price = contract_request.total_amount
                journal = self.env['account.journal'].sudo().search([('type', 'in', ['sale'])], limit=1)

                invoice = self.env['account.move'].sudo().create({
                    'move_type': 'out_invoice',
                    'partner_id': contract_request.partner_id.id,
                    'invoice_date': date.today(),
                    'journal_id': journal.id,
                    'currency_id': self.currency_id.id,
                    'invoice_payment_term_id': contract_request.payment_term_id.id or False,
                    'contract_req_id': self.id,
                    'invoice_line_ids': [
                        (0, 0, {
                            'product_id': product.id if product else False,
                            'name': product.name if product else False,
                            'quantity': 1,
                            'price_unit': price,
                        })]
                })

                invoice.action_post()
                self.write({'state': 'invoice', 'invoice_id': invoice.id})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }

    def view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }

    def request_send(self):
        """email send button"""
        self.send_mail()
        self.write({
            'state': 'send'
        })

    def button_approve(self):
        """approve button"""

        self.write({
            'state': 'approve'
        })
        self.send_mail()

    def button_reject(self):
        """reject button"""
        self.write({
            'state': 'reject'
        })
        # self.send_mail()

    def button_extend(self):
        """Button for extending the contract"""
        for record in self:
            # Duplicate the record with all its field values
            duplicated_record = record.copy()
            duplicated_record.name = "EX" + record.name + "-" + duplicated_record.name
            duplicated_record.parent_id = record.id
            return {
                'name': 'Extend Contract',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'project.contract.request',
                'res_id': duplicated_record.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def get_extended_contracts(self):
        """Smart button to show extended contracts"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extended',
            'view_mode': 'tree,form',  # Specify view modes as a list
            'res_model': 'project.contract.request',
            'domain': [('parent_id', '=', self.id)],
            'context': {'create': False}  # Context should be a dictionary
        }


class ProjectEngagement(models.Model):
    _name = 'project.engagement'

    name = fields.Char('Name')
    no_month = fields.Integer('No of Months')


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_req_id = fields.Many2one('project.contract.request', string='Offshore', )


class ProjectContractRequestAmc(models.Model):
    _name = 'project.contract.request.amc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "AMC"

    name = fields.Char('Name', default=lambda self: _('New'), copy=False)
    contract_type = fields.Selection([('onsite', 'Onsite'), ('offshore', 'Offshore')], 'Contract Type',
                                     default='onsite')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)

    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    po_no = fields.Char('Contract Number', copy=False, readonly=True, index=True, default=lambda self: _(''))
    date_sign = fields.Date('Sign Date', copy=False)
    date_contract = fields.Date('Contract Date', copy=False)
    date_start = fields.Date('Start Date', default=fields.Date.context_today, copy=False)
    date_end = fields.Date('End Date')
    project_id = fields.Many2one('project.project', 'Project')
    engagement_id = fields.Many2one('project.engagement', 'Contract Period')
    recurring_id = fields.Many2one('recurrence.period', 'Recurrence Period')
    provision_contracts = fields.Selection([('subscription', 'Subscription'), ('invoice', 'Invoice')],
                                           'Direct Invoice/Subscription',
                                           default='subscription')
    level1 = fields.Char('Level 1')
    level2 = fields.Char('Level 2')
    level3 = fields.Char('Level 3')
    parent_id = fields.Many2one('project.contract.request.amc', copy=False)

    industry = fields.Char('Industry')
    terms = fields.Html(string='Terms&Conditions')
    amc_bool = fields.Boolean('AMC', default=True)
    # attachments = fields.Binary('Attachment')
    attach_amc_ids = fields.Many2many('ir.attachment',
                                      'attach_rel_amc_',
                                      string="Attachment",
                                      help='You can attach the copy of your'
                                           ' document.', copy=False)
    resource_id = fields.Many2many('res.users', string='Resources')
    contact_count = fields.Float('Contracts', default=0, compute='compute_contracts')

    state = fields.Selection([
        ('draft', 'Hold'),
        ('send', 'Request Send'),
        ('sign', 'Signed'),
        ('approve', 'Active'),
        ('complete', 'Completed'),
        ('reject', 'Cancelled'),
        ('invoice', 'Invoiced'),
        ('expire', 'Expired'),
        ('paid', "Paid"),
        ('partial', "Partially Paid"),
        ('subscription', 'Subscription Created'),
    ], string='Status', default='draft', tracking=True)
    total_amount = fields.Float(string="Total Amount", required=True)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    invoice_id = fields.Many2one('account.move', string='Invoice', )
    plan_id = fields.Many2one('subscription.package.plan', 'Subscription Plan')
    subscription_id = fields.Many2one('subscription.package', string='Subscription',copy=False )
    allowed_company_ids = fields.Many2many('res.company',string='Visible Companies', default=lambda self: self.env.company.ids)


    def create_subscription(self):
        if self.plan_id:
            product_id = self.env.ref('kg_contracts.product_product_amc_subscription_').id

            if product_id:
                product = self.env['product.product'].browse(product_id)
                subscription = self.env['subscription.package'].sudo().create({
                    'partner_id': self.partner_id.id,
                    'start_date': self.date_start,
                    'currency_id': self.currency_id.id,
                    'reference_code': False,
                    'recurrence_period_id': self.recurring_id.id,
                    'plan_id': self.plan_id.id,
                    'contract_amc_id':self.id,
                    'product_line_ids': [
                        (0, 0, {
                            'product_id': product.id if product else False,
                            'product_qty': 1,
                        })]
                })
                subscription_list = subscription
                subscription_id = subscription_list[0].id

                # subscription.action_post()
                self.write({'state': 'subscription', 'subscription_id': subscription_id})

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Subscriptions',
                    'res_model': 'subscription.package',
                    'res_id': self.subscription_id.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'current',
                }
        else:
            raise ValidationError('Choose a Subscription plan')

    def complete_button(self):
        """Complete Button"""
        for rec in self:
            rec.state = 'complete'

    def cron_action_to_expire(self):
        """cron action to expire expired contracts"""
        today = fields.Date.today()
        for rec in self.search([]):
            if rec.date_end and rec.date_end <= today:
                rec.write({
                    'state': 'expire'
                })

    def view_subs(self):
        self.ensure_one()
        if not self.subscription_id:
            raise ValidationError("No subscription linked to this record.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subscriptions',
            'res_model': 'subscription.package',
            'res_id': self.subscription_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }

    def compute_contracts(self):
        for record in self:
            record.contact_count = self.env['project.contract.request.amc'].search_count(
                [('parent_id', '=', self.id)])

    from datetime import date, timedelta



    def action_contract_end_date_over(self):
        """Action for scheduling an action for ending date"""
        current_date = date.today()
        target_date = current_date + timedelta(days=2)  # Calculate the target date, two days from today

        contracts_ending = self.env['project.contract.request.amc'].search([
            ('date_end', '=', target_date), ('state', 'not in', ('draft', 'cancel'))
        ])

        if contracts_ending:
            for contract in contracts_ending:
                data_config = self.env['res.config.settings'].sudo().search([])
                group_send_mail = []

                for config_rec in data_config.contract_approval_ids:
                    if config_rec.email:
                        group_send_mail.append(config_rec.email)

                subject = _('AMC Contract Is Expiring')
                body = _('AMC Contract is expiring in two days for customer "%s".') % (
                    contract.partner_id.name)

                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': ', '.join(group_send_mail),
                }
                self.env['mail.mail'].create(mail_values).send()

    @api.model_create_multi
    def create(self, vals_list):
        """ Create a sequence for the contract request model """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('contract.reference.amc')
                vals['name'] = sequence
            if vals.get('po_no', _('')) == _(''):
                sequence = self.env['ir.sequence'].next_by_code('amc.number.contract')
                vals['po_no'] = sequence
        return super().create(vals_list)

    @api.onchange('date_start', 'recurring_id')
    def on_change_contract_recurrence(self):
        # if not self.date_start or not self.recurring_id:
        #     self.confirmation_date = False
        #     return

        unit = self.recurring_id.unit
        duration = self.recurring_id.duration

        if unit == 'years':
            confirmation_date = self.date_start + relativedelta(years=duration, days=-1)
        elif unit == 'days':
            confirmation_date = self.date_start + relativedelta(days=duration - 1)
        elif unit == 'months':
            confirmation_date = self.date_start + relativedelta(months=duration, days=-1)
        elif unit == 'weeks':
            confirmation_date = self.date_start + relativedelta(weeks=duration, days=-1)
        elif unit == 'hours':
            confirmation_date = self.date_start + relativedelta(hours=duration)
        else:
            confirmation_date = False
        self.write({
            "date_end": confirmation_date

        })

    @api.onchange('amc_bool')
    def on_change_amc_periode(self):
        """set contract period for Amc"""
        contract = self.env['project.engagement'].search([('no_month', '=', 12)])
        self.engagement_id = False
        if self.amc_bool:
            self.write({
                "engagement_id": contract.id

            })

    def send_mail(self):
        """Send email to approves"""
        data_config = self.env['res.config.settings'].sudo().search([])
        group_send_mail = []

        for config_rec in data_config.contract_approval_ids:
            if config_rec.email:
                group_send_mail.append(config_rec.email)

        subject = _('AMC Contract  for : %s') % self.partner_id.name
        body = _('AMC Contract  has been Confirmed for customer "%s".') % (
            self.partner_id.name)

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        url = "{}/web#id={}&view_type=form&model={}".format(base_url, self.id, self._name)

        link_tag = "<a href='{}'>{}</a>".format(url, "Click here to view")

        mail_values = {
            'subject': subject,
            'body_html': body + "<br/>" + link_tag,
            'email_to': ', '.join(group_send_mail),
        }
        self.env['mail.mail'].create(mail_values).send()

    def request_send(self):
        """email send button"""
        self.send_mail()
        self.write({
            'state': 'send'
        })

    def button_approve(self):
        if not self.project_id:
            raise ValidationError('Choose a Project')
        """approve button"""

        self.write({
            'state': 'approve'
        })
        self.send_mail()


    def button_reject(self):
        """reject button"""
        self.write({
            'state': 'reject'
        })

    def button_extend(self):
        """Button for extending the contract"""
        for record in self:
            # Duplicate the record with all its field values
            duplicated_record = record.copy()
            duplicated_record.name = "RE" + record.name + "-" + duplicated_record.name
            contract_id = self.search(
                [('parent_id', '=', record.id)], limit=1, order='name desc')
            if contract_id:
                duplicated_record.date_start = contract_id.date_end + timedelta(days=1)
            else:
                duplicated_record.date_start = record.date_end + timedelta(days=1)
            duplicated_record.parent_id = record.id
            duplicated_record.on_change_contract_recurrence()

            return {
                'name': 'Extend Contract',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'project.contract.request.amc',
                'res_id': duplicated_record.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def get_extended_contracts(self):
        """Smart button to show extended contracts"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extended',
            'view_mode': 'tree,form',  # Specify view modes as a list
            'res_model': 'project.contract.request.amc',
            'domain': [('parent_id', '=', self.id)],
            'context': {'create': False}  # Context should be a dictionary
        }

    def create_invoice(self):
        for contract_request in self:
            product_id = self.env.ref('kg_contracts.product_product_amc').id

            if product_id:
                product = self.env['product.product'].browse(product_id)
                price = contract_request.total_amount
                journal = self.env['account.journal'].sudo().search([('type', 'in', ['sale'])], limit=1)

                invoice = self.env['account.move'].sudo().create({
                    'move_type': 'out_invoice',
                    'partner_id': contract_request.partner_id.id,
                    'invoice_date': date.today(),
                    'currency_id': self.currency_id.id,
                    'journal_id': journal.id,
                    'invoice_payment_term_id': contract_request.payment_term_id.id or False,
                    'invoice_line_ids': [
                        (0, 0, {
                            'product_id': product.id if product else False,
                            'name': product.name if product else False,
                            'quantity': 1,
                            'price_unit': price,
                        })]
                })
                self.write({'state': 'invoice', 'invoice_id': invoice.id})
                invoice.action_post()
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Invoice',
                    'res_model': 'account.move',
                    'res_id': self.invoice_id.id,
                    'view_mode': 'form',
                    'view_type': 'form',
                    'target': 'current',
                }

    def view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }

class AccountPaymentRegisterInh(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        payments = self._create_payments()
        invoices = payments.reconciled_invoice_ids
        subscription_ids = invoices.mapped('subscription_id')
        subscription_records = self.env['project.contract.request.amc'].search([
            ('subscription_id', 'in', subscription_ids.ids)
        ])
        subscription_records_req = self.env['project.contract.request'].search([
            ('subscription_id', 'in', subscription_ids.ids)
        ])
        for subscription in subscription_records:
            related_invoices = subscription.subscription_id.sale_order_id.order_line.invoice_lines.move_id.filtered(
                lambda r: r.move_type in ('out_invoice', 'out_refund')
            )
            if any(inv.payment_state == 'partial' for inv in related_invoices):
                subscription.state = 'partial'
            elif all(inv.payment_state == 'paid' for inv in related_invoices):
                subscription.state = 'paid'

        for sub_req in subscription_records_req:
            related_invoices = sub_req.subscription_id.sale_order_id.order_line.invoice_lines.move_id.filtered(
                lambda r: r.move_type in ('out_invoice', 'out_refund')
            )
            if any(inv.payment_state == 'partial' for inv in related_invoices):
                sub_req.state = 'partial'
            elif all(inv.payment_state == 'paid' for inv in related_invoices):
                sub_req.state = 'paid'

        for invoice in invoices:
            amc_records = self.env['project.contract.request.amc'].search([
                ('invoice_id', '=', invoice.id)
            ])
            for amc in amc_records:
                if invoice.payment_state == 'partial':
                    amc.state = 'partial'
                elif invoice.payment_state == 'paid':
                    amc.state = 'paid'
        for invoice in invoices:
            contract_req_records = self.env['project.contract.request'].search([
                ('invoice_id', '=', invoice.id)
            ])
            for con_req in contract_req_records:
                if invoice.payment_state == 'partial':
                    con_req.state = 'partial'
                elif invoice.payment_state == 'paid':
                    con_req.state = 'paid'

        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action





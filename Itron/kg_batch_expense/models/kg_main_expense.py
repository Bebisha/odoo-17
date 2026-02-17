from datetime import date, datetime

from pkg_resources import require

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KgMainExpense(models.Model):
    _name = 'kg.main.expense'
    _description = 'Main Expenses'
    _rec_name = 'name'

    name = fields.Char("Name", required=True)
    sub_category_ids = fields.Many2many('product.product', string="Sub Category",
                                        domain="[('can_be_expensed', '=', True)]")


class BatchExpense(models.Model):
    _name = 'kg.batch.expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Batch Expenses'
    _rec_name = 'category_id'

    category_id = fields.Many2one('kg.main.expense', string="Name", required=True)
    payment_mode = fields.Selection(
        selection=[
            ('own_account', "Employee (to reimburse)"),
            ('company_account', "Company")
        ],
        string="Paid By",
        default='own_account',
        tracking=True,
    )
    state = fields.Selection([
        ('drafts', 'Draft'),
        ('draft', 'Confirmed'),
        ('1st_approve', 'Waiting For Second Approval'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ], default='drafts')
    batch_line_ids = fields.One2many('batch.expense.line', 'batch_line_id', string="Batch Line")
    is_expense_approver = fields.Boolean(
        string="Is Expense Approver",
        compute="_compute_is_expense_approver",
        store=False
    )
    is_expense_approver_sec = fields.Boolean(
        string="Is Expense Approver",
        compute="_compute_is_expense_approver_sec",
        store=False
    )
    employee_id = fields.Many2one('hr.employee', readonly=True, related='batch_line_ids.employee_id')

    def get_expense(self):
        """ function smart tab to show the expense """
        self.ensure_one()
        domain = []
        expense = self.env['hr.expense'].search([('batch_id', '=', self.id)])
        for rec in expense:
            domain.append(rec.sheet_id.id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense',
            'view_mode': 'tree,form',
            'res_model': 'hr.expense.sheet',
            'context': "{'create':'False'}",
            'domain': [('id', 'in', domain)]
        }

    def _compute_is_expense_approver(self):
        expense_approval_ids = self.env['ir.config_parameter'].sudo().get_param('expense_approval_ids')
        group_approvers = []
        if expense_approval_ids:
            for config_rec in self.env['res.users'].browse(eval(expense_approval_ids)):
                if config_rec.email:
                    group_approvers.append(config_rec.id)
            for rec in self:
                if self.env.user.id in group_approvers:
                    rec.write({
                        'is_expense_approver': True,
                    })
                else:
                    rec.write({
                        'is_expense_approver': False,
                    })
        else:
            self.write({
                'is_expense_approver': False,
            })

    def _compute_is_expense_approver_sec(self):
        expense_approval_ids = self.env['ir.config_parameter'].sudo().get_param('expense_sec_approval_ids')
        group_approvers = []
        if expense_approval_ids:
            for config_rec in self.env['res.users'].browse(eval(expense_approval_ids)):
                if config_rec.email:
                    group_approvers.append(config_rec.id)
            for rec in self:
                if self.env.user.id in group_approvers:
                    rec.write({
                        'is_expense_approver_sec': True,
                    })
                else:
                    rec.write({
                        'is_expense_approver_sec': False,
                    })
        else:
            self.write({
                'is_expense_approver_sec': False,
            })

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.category_id:
            self.batch_line_ids = False
            sub_categories = self.category_id.sub_category_ids
            for sub_category in sub_categories:
                self.batch_line_ids = [(0, 0, {
                    'product_id': sub_category.id,
                })]

    def action_confirmed(self):
        self.write({'state': 'draft'})
        for line in self.batch_line_ids:
            my_expense_vals = {
                'name': line.name,
                'date': line.date,
                'employee_id': line.employee_id.id,
                'product_id': line.product_id.id,
                'total_amount_currency': line.total,
                'payment_mode': self.payment_mode,
                'batch_id': self.id,
                'parent_category_id': self.category_id.id

            }
            expense = self.env['hr.expense'].create(my_expense_vals)
        expense_approval_ids = self.env['ir.config_parameter'].sudo().get_param('expense_approval_ids')
        group_send_mail = []
        if expense_approval_ids:
            for config_rec in self.env['res.users'].browse(eval(expense_approval_ids)):
                if config_rec.email:
                    group_send_mail.append(config_rec.email)

            button_style = (
                "display: inline-block; padding: 10px 10px; font-size: 16px; "
                "color: white; background-color: #007bff; text-decoration: none; "
                "border-radius: 5px;"
            )
            subject = _('Expense Approval  Request')
            body = _(
                "<p>Dear Sir/Ma'am,</p>"
                "<p>An expense request has been submitted by <strong>{employee_name} </strong>and requires your approval.</p>"
                "<p><strong>Expense Details:</strong></p>"
                "<p><a href='{url}' style='{style}'>View</a></p>"
                "<p>Please review and approve the expense at your earliest convenience.</p>"
                "<p>Thank you.</p>"
                "<p>Best regards,<br>Your Team</p>"
            ).format(
                employee_name=self.employee_id.name,
                url=f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={self.id}&view_type=form&model=kg.batch.expense",
                style=button_style,
            )
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            # approve_url = "{}/web/action_first_approve?id={}".format(base_url, self.id)
            # reject_url = "{}/web/action_reject?id={}".format(base_url, self.id)
            #
            # html_content = """
            #                         <div>
            #                              <a href="{}">
            #                                      <button style='padding:7px;background-color:#28a745;color:white;
            #                                      height:35px;border-radius:10px;margin-left:10px;'>
            #                         APPROVE
            #                     </button>
            #                 </a>
            #                 <a href="{}">
            #                                      <button style='padding:7px;background-color:#AF1740;color:white;
            #                                      height:35px;border-radius:10px;margin-left:10px;'>
            #                         Reject
            #                     </button>
            #                 </a>
            #                         </div>
            #                     """.format(approve_url, reject_url)
            mail_values = {
                'subject': subject,
                'body_html': body + "<br/>",
                'email_to': ', '.join(group_send_mail),
            }
            self.env['mail.mail'].sudo().create(mail_values).send()
        else:
            raise ValidationError(
                _('No expense approvers are configured in the system. Please set approvers in system settings.'))

    def action_first_approve(self):
        self.write({'state': '1st_approve'})
        expense_approval_ids = self.env['ir.config_parameter'].sudo().get_param('expense_sec_approval_ids')
        group_send_mail = []
        if expense_approval_ids:
            for config_rec in self.env['res.users'].browse(eval(expense_approval_ids)):
                if config_rec.email:
                    group_send_mail.append(config_rec.email)
            button_style = (
                "display: inline-block; padding: 10px 10px; font-size: 16px; "
                "color: white; background-color: #007bff; text-decoration: none; "
                "border-radius: 5px;"
            )
            subject = _('Expense Approval  Request')
            body = _(
                "<p>Dear Sir/Ma'am,</p>"
                "<p>An expense request has been submitted by <strong>{employee_name}</strong> and requires your approval.</p>"
                "<p><strong>Expense Details:</strong></p>"
                "<p><a href='{url}' style='{style}'>View</a></p>"
                "<p>Please review and approve the expense at your earliest convenience.</p>"
                "<p>Thank you.</p>"
                "<p>Best regards,<br>Your Team</p>"
            ).format(
                employee_name=self.employee_id.name,
                url=f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={self.id}&view_type=form&model=kg.batch.expense",
                style=button_style,
            )
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': ', '.join(group_send_mail),
            }
            self.env['mail.mail'].sudo().create(mail_values).send()

    def action_approve(self):
        len_po = 0
        self.write({'state': 'approved'})
        expense = self.env['hr.expense'].search([('batch_id', '=', self.id)])
        for exp in expense:
            exp.action_submit_expenses()
            exp.sheet_id._do_approve()
            exp.sheet_id.action_sheet_move_create()

    def action_reject(self):
        print('vishnu')
        expense = self.env['hr.expense'].search([('batch_id', '=', self.id)])
        self.write({'state': 'refused'})
        expense.write({
            'state': 'refused'
        })

    def action_journal_entry(self):
        expense = self.env['hr.expense'].search([('batch_id', '=', self.id)])
        sheet = expense.sheet_id.mapped('account_move_ids')
        return {
            'name': 'Journal Entries',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', sheet.ids)],
            'type': 'ir.actions.act_window',
        }


class HrExpenseLine(models.Model):
    _name = 'batch.expense.line'

    @api.model
    def _domain_employee(self):
        if self.env.user.has_group('base.group_system'):
            return []  # No restriction for admins
        return [('user_id', '=', self.env.uid)]

    name = fields.Char(string="Description", required=True)
    product_id = fields.Many2one('product.product', string="Category", required=True,
                                 domain="[('can_be_expensed', '=', True), ('id', 'in', available_product_ids)]")
    total = fields.Float(string="Total", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,
                                  domain=lambda self: self._domain_employee(), )

    date = fields.Date(string="Expense Date", default=fields.Date.context_today)

    batch_line_id = fields.Many2one('kg.batch.expense', string="Batch Line")
    available_product_ids = fields.Many2many('product.product', compute='_compute_available_products')

    @api.model
    def default_get(self, fields):
        res = super(HrExpenseLine, self).default_get(fields)
        if 'employee_id' in fields:
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
            res['employee_id'] = employee.id
        return res

    @api.constrains('total')
    def _check_total(self):
        for record in self:
            if record.total <= 0.0:
                raise ValidationError("The total must be greater than zero.")

    @api.depends('batch_line_id.category_id.sub_category_ids')
    def _compute_available_products(self):
        for line in self:
            if line.batch_line_id and line.batch_line_id.category_id:
                line.available_product_ids = line.batch_line_id.category_id.sub_category_ids
            else:
                line.available_product_ids = False


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    batch_id = fields.Many2one('kg.batch.expense', string="Batch id")
    parent_category_id = fields.Many2one('kg.main.expense', string="Parent Category", readonly=True)
    state = fields.Selection(
        selection=[
            ('draft', 'To Report'),
            ('reported', 'To Submit'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('paid', 'Paid'),
            ('done', 'Done'),
            ('refused', 'Refused')
        ],
        string="Status",
        compute='_compute_state', store=True, readonly=True,
        index=True,
        copy=False,
        default='draft',
    )



    @api.depends('sheet_id', 'sheet_id.account_move_ids', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id:
                expense.state = 'draft'
            elif expense.sheet_id.state == 'draft':
                expense.state = 'reported'
            elif expense.sheet_id.state == 'cancel':
                expense.state = 'refused'
            elif expense.sheet_id.state == 'approve':
                expense.state = 'approved'
            elif expense.sheet_id.state == 'post':
                expense.state = 'paid'
            elif not expense.sheet_id.account_move_ids:
                expense.state = 'submitted'
            else:
                expense.state = 'done'

    def action_open_payment_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense Payment',
            'res_model': 'expense.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_expense_ids': self.ids,
            }
        }


class HrExpense(models.Model):
    _inherit = 'hr.expense.sheet'

    state = fields.Selection(
        selection=[
            ('draft', 'To Submit'),
            ('submit', 'Submitted'),
            ('approve', 'Approved'),
            ('post', 'Paid'),
            ('done', 'Done'),
            ('cancel', 'Refused')
        ],
        string="Status",
        compute='_compute_state', store=True, readonly=True,
        index=True,
        required=True,
        default='draft',
        tracking=True,
        copy=False,
    )

    paid_on = fields.Date('Payment Date')

    def action_paid(self):
        """Function to handle payment processing."""
        if not self.paid_on:
            raise ValidationError('Please add the payment date before proceeding')
        self.write({'state': 'post'})
        # for rec in self:
        #     for line in rec.expense_line_ids:
        #         line.write({'state': 'paid'})

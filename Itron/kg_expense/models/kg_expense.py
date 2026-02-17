from datetime import date, datetime

from odoo import models, fields, api


class KgExpense(models.Model):
    _name = 'kg.expense'
    _description = 'Expenses'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    number = fields.Char(string="Expense number", default="/", readonly=True)
    name = fields.Char("Name")
    expense_line_ids = fields.One2many("kg.expense.line", 'expense_line_id', ondelete="cascade")
    expense_date = fields.Date("Expense Date")
    employee_id = fields.Many2one('hr.employee')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    # company_ids = fields.Many2many('res.company', 'kg_expense_company',
    #                                string='Companies', default=lambda self: self.env.company.ids)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=False, store=True,
                                  default=lambda self: self.env.company.currency_id)
    total = fields.Float("Total", compute='compute_total')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], default='draft')

    @api.onchange('expense_date')
    def expense_date_expense_date(self):
        today = datetime.now().date()
        self.expense_date = today.strftime("%Y-%m-%d")

    @api.depends('expense_line_ids')
    def compute_total(self):
        self.total = sum(self.expense_line_ids.mapped('cost'))

    def action_submit(self):
        self.write({'state': 'waiting'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'refused'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def create(self, vals):
        if vals.get("number", "/") == "/":
            vals["number"] = self._prepare_expense_number(vals)
        res = super().create(vals)
        return res

    def _prepare_expense_number(self, values):
        seq = self.env["ir.sequence"]
        if "company_id" in values:
            seq = seq.with_company(values["company_id"])
        return seq.next_by_code("expense.sequence") or "/"


class KgExpenseLine(models.Model):
    _name = 'kg.expense.line'
    _description = 'Category Line'

    expense_line_id = fields.Many2one('kg.expense')
    category_id = fields.Many2one('kg.expense.category')
    cost = fields.Float("Cost")
    attachment_ids = fields.Many2many(
        'ir.attachment', 'expense_doc_rel', string="Attach File")


class KgExpenseCategory(models.Model):
    _name = 'kg.expense.category'
    _description = 'category'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    category_name = fields.Char('Name', required=True)
    internal_ref = fields.Char("Internal Reference", required=True)
    # cost = fields.Float("Cost")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    name = fields.Char("Product", compute="_compute_product_name", invisible=1)
    image_1920 = fields.Image()
    note = fields.Html()

    @api.depends('internal_ref', 'category_name')
    def _compute_product_name(self):
        for record in self:
            record.name = False
            if record.internal_ref and record.category_name:
                record.name = str('[ %s ]  %s' % (record.internal_ref,
                                                  record.category_name))
            else:
                record.name = False

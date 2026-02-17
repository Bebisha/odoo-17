from odoo import models, fields, api,_
from odoo.tools import formatLang
from odoo.exceptions import ValidationError


class KGAccountMoveInherit(models.Model):
    _inherit = "account.move"

    division_id = fields.Many2one("kg.divisions", string="Division")
    is_freight_bill = fields.Boolean(default=False, string="Is Freight Bill", copy=False)
    boe_ref = fields.Char(string="BOE Reference")

    freight_custom = fields.Monetary(string="Freight", currency_field="currency_id",
                                     help="Freight charges for this order.")
    custom_charge = fields.Monetary(string="Custom", currency_field="currency_id",
                                    help="Customs charges for this order.")
    type_id = fields.Selection([('local', 'Local'), ('meast', 'Middle east'), ('international', 'International'),
                                ('sisconcern', 'Sister Concern'), ('subcontracting', 'Subcontracting')],
                               default='sisconcern', string="Type", related='partner_id.po_type', store=True)

    partner_invoice_id = fields.Many2one(
        comodel_name='res.partner',
        string="Invoice Address",
        compute='_compute_partner_invoice_id',
        store=True, readonly=False, required=True, precompute=True,
        check_company=True,
        index='btree_not_null')

    vessel_id = fields.Many2one("vessel.code",string="Vessel")

    @api.constrains('invoice_date', 'date')
    def _check_accounting_date(self):
        for record in self:
            if not record.invoice_date or not record.date:
                continue
            today = fields.Date.context_today(record)
            # if record.invoice_date < today:
            #     raise ValidationError("The Invoice Date cannot be earlier than today's date.")
            if record.date < today:
                raise ValidationError("Accounting Date cannot be earlier than today's date.")
            if record.date < record.invoice_date:
                raise ValidationError("Accounting date cannot be less than Bill/Invoice Date")

    @api.depends('invoice_date', 'company_id')
    def _compute_date(self):
        for move in self:
            if not move.invoice_date:
                if not move.date:
                    move.date = fields.Date.context_today(self)
                continue
            accounting_date = fields.Date.context_today(self)
            print(accounting_date, "accounting_date")
            if not move.is_sale_document(include_receipts=True):
                accounting_date = move._get_accounting_date(move.invoice_date, move._affect_tax_report())
            if accounting_date and accounting_date != move.date:
                move.date = fields.Date.context_today(self)
                # _affect_tax_report may trigger premature recompute of line_ids.date
                self.env.add_to_compute(move.line_ids._fields['date'], move.line_ids)
                # might be protected because `_get_accounting_date` requires the `name`
                self.env.add_to_compute(self._fields['name'], move)


    @api.depends('partner_id')
    def _compute_partner_invoice_id(self):
        for order in self:
            order.partner_invoice_id = order.partner_id.address_get(['invoice'])['invoice'] if order.partner_id else False

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.balance',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'state', 'freight_custom', 'custom_charge')
    def _compute_amount(self):
        res = super(KGAccountMoveInherit, self)._compute_amount()
        for move in self:
            total_freight_custom = move.freight_custom + move.custom_charge
            move.amount_total += total_freight_custom
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.type_id = self.partner_id.po_type


class KGAccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    has_abnormal_deferred_dates = fields.Char()
    division_id = fields.Many2one("kg.divisions", string="Division")


class InvoicePaymentWizard(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'
    _description = 'Invoice payment on delivery'

    has_timer_running = fields.Char()


class AccountPayment(models.Model):

    _inherit = "account.payment"

    type_id = fields.Selection([('local', 'Local'), ('meast', 'Middle east'), ('international', 'International'),
                                ('sisconcern', 'Sister Concern'), ('subcontracting', 'Subcontracting')],
                               default='sisconcern', string="Type", related='partner_id.po_type', store=True)


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.type_id = self.partner_id.po_type
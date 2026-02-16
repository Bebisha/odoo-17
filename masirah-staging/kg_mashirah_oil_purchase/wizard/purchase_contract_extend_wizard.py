from datetime import date

from odoo.exceptions import ValidationError
from odoo import models, fields, api


class PurchaseContractExtendWizard(models.TransientModel):
    _name = "purchase.contract.extend.wizard"
    _description = "Purchase Contract Extend Wizard"

    name = fields.Char(string="Reference")
    purchase_contract_id = fields.Many2one('purchase.contract.agreement', string="Purchase Contract")
    purchase_contract_extend_line_ids = fields.One2many("purchase.contract.extend.line.wizard",
                                                        'purchase_contract_extend_line_id', string="Extend Lines")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.onchange('start_date', 'end_date')
    def get_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                for line in rec.purchase_contract_extend_line_ids:
                    line.start_date = rec.start_date
                    line.end_date = rec.end_date

    def apply(self):
        vals = []
        if self.purchase_contract_extend_line_ids:
            if any(not li.start_date or not li.end_date for li in self.purchase_contract_extend_line_ids):
                raise ValidationError("The Start Date and End Date are required!!!")

            for line in self.purchase_contract_extend_line_ids:
                if any(li.start_date and li.end_date and
                       line.start_date <= li.end_date and line.end_date >= li.start_date and li.product_id.id == line.product_id.id
                       for li in self.purchase_contract_id.purchase_contract_ids):
                    raise ValidationError('You cannot have two Purchase Contracts on the same day!')

                vals.append((0, 0, {
                    'start_date': line.start_date,
                    'end_date': line.end_date,
                    'product_id': line.product_id.id,
                    'unit_price': line.unit_price,
                    'description': line.description,
                    'uom_id': line.uom_id.id,
                }))
            self.purchase_contract_id.write({'purchase_contract_ids': vals})


class PurchaseContractExtendLineWizard(models.TransientModel):
    _name = "purchase.contract.extend.line.wizard"
    _description = "Purchase Contract Extend Line Wizard"

    name = fields.Char(string="Reference")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    product_id = fields.Many2one("product.product", string="Product")
    unit_price = fields.Float(string="Unit Price")
    purchase_contract_extend_line_id = fields.Many2one('purchase.contract.extend.wizard',
                                                       string="Purchase Contract Extend")
    description = fields.Char(string="Description")
    uom_id = fields.Many2one("uom.uom", string="UOM")

    @api.onchange('start_date', 'end_date')
    def check_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')

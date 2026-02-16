from base64 import encodebytes
from datetime import datetime
from io import BytesIO

from odoo import models, fields, api
from odoo.exceptions import UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class VatReturnReport(models.TransientModel):
    _name = 'vat.return.report'

    date_from = fields.Date("Start Date")
    date_to = fields.Date("End Date")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)
    target_moves = fields.Selection([('all_posted_entries', 'All Posted Entries'), ('all_entries', 'All Entries')],
                                    default='all_posted_entries')

    @api.onchange('date_from', 'date_to')
    def onchange_date(self):
        if (self.date_from and self.date_to) and (self.date_from > self.date_to):
            raise UserError("End date must be greater than start date!  ")

    def get_values(self, company):
        value_list = []
        value_dict = {
            'sales': [],
            'purchase': []
        }
        domain = [('company_id', '=', company.id), ('date', '>=', self.date_from), ('date', '<=', self.date_to)]
        if self.target_moves == 'all_posted_entries':
            domain.append(('parent_state', '=', 'posted'))
        account_move_lines = self.env['account.move.line'].sudo().search(domain)
        # ----outside gcc supplies----
        tax_group_outside_gcc = self.env['account.tax.group'].search(
            [('id', '=', self.env.ref('kg_mashirah_oil_accounting.outside_gcc_supplies').id),
             ('company_id', '=', company.id)])
        taxes_outside_gcc = self.env['account.tax'].sudo().search([]).filtered(
            lambda x: x.type_tax_use == 'sale' and x.tax_group_id == tax_group_outside_gcc)
        group_outside_gcc = {
            'group': tax_group_outside_gcc.name,
            "taxes": [],
            'total_taxable': False,
            'total_tax': False
        }
        gcc_outside_sales_taxable_amount = 0
        gcc_outside_sales_tax_amount = 0

        for tax in taxes_outside_gcc:
            taxes_outside_gcc_tax_export = account_move_lines.filtered(lambda x: x.name == tax.name)
            gcc_outside_sales_taxable_amount += sum(taxes_outside_gcc_tax_export.mapped('move_id.amount_untaxed'))
            gcc_outside_sales_tax_amount += sum(taxes_outside_gcc_tax_export.mapped('credit'))
            group_outside_gcc["taxes"].append({
                'name': tax.name,
                'base_amount': sum(taxes_outside_gcc_tax_export.mapped('move_id.amount_untaxed')),
                'amount': sum(taxes_outside_gcc_tax_export.mapped('credit'))

            })
            group_outside_gcc["total_taxable"] = gcc_outside_sales_taxable_amount
            group_outside_gcc["total_tax"] = gcc_outside_sales_tax_amount
        if group_outside_gcc["taxes"]:
            value_dict['sales'].append(group_outside_gcc)

        # ----local_purchase----

        tax_group_local_purchase = self.env['account.tax.group'].sudo().search(
            [('id', '=', self.env.ref('kg_mashirah_oil_accounting.local_purchase').id),
             ('company_id', 'in', [False, company.id])])
        taxes_local_purchase = self.env['account.tax'].sudo().search([]).filtered(
            lambda x: x.type_tax_use == 'purchase' and x.tax_group_id == tax_group_local_purchase)
        group_local_purchase = {
            'group': tax_group_local_purchase.name,
            "taxes": [],
            'total_taxable': False,
            'total_tax': False

        }
        local_purchase_taxable_amount = 0
        local_purchase_tax_amount = 0
        for tax in taxes_local_purchase:
            local_purchase_tax_export = account_move_lines.filtered(lambda x: x.name == tax.name)
            group_local_purchase["taxes"].append({
                'name': tax.name,
                'base_amount': sum(local_purchase_tax_export.mapped('move_id.amount_untaxed')),
                'amount': sum(local_purchase_tax_export.mapped('debit'))

            })
            local_purchase_taxable_amount += sum(local_purchase_tax_export.mapped('move_id.amount_untaxed'))
            local_purchase_tax_amount += sum(local_purchase_tax_export.mapped('debit'))

            group_local_purchase["total_taxable"] = local_purchase_taxable_amount
            group_local_purchase["total_tax"] = local_purchase_tax_amount

        # if group_local_purchase["taxes"]:
        #     value_dict['purchase'].append(group_local_purchase)

        tax_group_gcc_purchase = self.env['account.tax.group'].sudo().search(
            [('id', '=', self.env.ref('kg_mashirah_oil_accounting.gcc_purchase').id),
             ('company_id', 'in', [False, company.id])])
        taxes_gcc_purchase = self.env['account.tax'].sudo().search([]).filtered(
            lambda x: x.type_tax_use == 'purchase' and x.tax_group_id == tax_group_gcc_purchase)
        group_gcc_purchase = {
            'group': tax_group_gcc_purchase.name,
            "taxes": [],
            'total_taxable': False,
            'total_tax': False
        }
        gcc_purchase_taxable_amount = 0
        gcc_purchase_tax_amount = 0
        for tax in taxes_gcc_purchase:
            gcc_purchase_tax_export = account_move_lines.filtered(lambda x: x.name == tax.name)
            group_gcc_purchase["taxes"].append({

                'name': tax.name,
                'base_amount': sum(gcc_purchase_tax_export.mapped('move_id.amount_untaxed')),
                'amount': sum(gcc_purchase_tax_export.mapped('debit'))

            })
            gcc_purchase_taxable_amount += sum(gcc_purchase_tax_export.mapped('move_id.amount_untaxed'))
            gcc_purchase_tax_amount += sum(gcc_purchase_tax_export.mapped('debit'))
            group_gcc_purchase["total_taxable"] = gcc_purchase_taxable_amount
            group_gcc_purchase["total_tax"] = gcc_purchase_tax_amount

        #
        # if group_gcc_purchase["taxes"]:
        #     value_dict['purchase'].append(group_gcc_purchase)

        tax_group_outside_gcc_purchase = self.env['account.tax.group'].sudo().search(
            [('id', '=', self.env.ref('kg_mashirah_oil_accounting.outside_gcc_purchase').id),
             ('company_id', 'in', [False, company.id])])
        taxes_outside_gcc_purchase = self.env['account.tax'].sudo().search([]).filtered(
            lambda x: x.type_tax_use == 'purchase' and x.tax_group_id == tax_group_outside_gcc_purchase)
        group_outside_gcc_purchase = {
            'group': tax_group_outside_gcc_purchase.name,
            "taxes": [],
            'total_taxable': False,
            'total_tax': False
        }
        outside_gcc_purchase_taxable_amount = 0
        outside_gcc_purchase_tax_amount = 0
        for tax in taxes_outside_gcc_purchase:
            outside_gcc_purchase_tax_export = account_move_lines.filtered(lambda x: x.name == tax.name)
            group_outside_gcc_purchase["taxes"].append({

                'name': tax.name,
                'base_amount': sum(outside_gcc_purchase_tax_export.mapped('move_id.amount_untaxed')),
                'amount': sum(outside_gcc_purchase_tax_export.mapped('debit'))

            })
            outside_gcc_purchase_taxable_amount += sum(outside_gcc_purchase_tax_export.mapped('move_id.amount_untaxed'))
            outside_gcc_purchase_tax_amount += sum(outside_gcc_purchase_tax_export.mapped('debit'))
            group_outside_gcc_purchase["total_taxable"] = outside_gcc_purchase_taxable_amount
            group_outside_gcc_purchase["total_tax"] = outside_gcc_purchase_tax_amount

        #
        # if group_outside_gcc_purchase["taxes"]:
        #     value_dict['purchase'].append(group_outside_gcc_purchase)

        tax_group_captial_goods = self.env['account.tax.group'].sudo().search(
            [('id', '=', self.env.ref('kg_mashirah_oil_accounting.capital_goods').id),
             ('company_id', 'in', [False, company.id])])
        taxes_captial_goods = self.env['account.tax'].sudo().search([]).filtered(
            lambda x: x.type_tax_use == 'purchase' and x.tax_group_id == tax_group_captial_goods)
        group_captial_goods = {
            'group': tax_group_captial_goods.name,
            "taxes": [],
            'total_taxable': False,
            'total_tax': False
        }
        captial_goods_taxable_amount = 0
        captial_goods_tax_amount = 0
        for tax in taxes_captial_goods:
            captial_goods_tax_export = account_move_lines.filtered(lambda x: x.name == tax.name)
            group_captial_goods["taxes"].append({
                'name': tax.name,
                'base_amount': sum(captial_goods_tax_export.mapped('move_id.amount_untaxed')),
                'amount': sum(captial_goods_tax_export.mapped('debit'))

            })
            captial_goods_taxable_amount += sum(captial_goods_tax_export.mapped('move_id.amount_untaxed'))
            captial_goods_tax_amount += sum(captial_goods_tax_export.mapped('debit'))
            group_captial_goods["total_taxable"] = captial_goods_taxable_amount
            group_captial_goods["total_tax"] = captial_goods_tax_amount
        group_local_purchase["total_taxable"] += captial_goods_taxable_amount
        group_local_purchase["total_tax"] += captial_goods_tax_amount

        sale_taxes = self.env['account.tax'].sudo().search([]).filtered(
            lambda x: x.type_tax_use == 'sale' and x.reverse_charge == True)
        purchase_taxes = self.env['account.tax'].sudo().search([]).filtered(
            lambda x: x.type_tax_use == 'purchase' and x.reverse_charge == True)
        sale_reverse_charge = 0
        sale_reverse_charge_taxable_amount = 0
        purchase_reverse_charge_taxable_amount = 0
        purchase_reverse_charge = 0
        for tax_id in sale_taxes:
            sale_reverse_charge_taxable_amount += sum(
                account_move_lines.filtered(lambda x: x.name == tax_id.name).mapped('move_id.amount_untaxed'))
            sale_reverse_charge += sum(account_move_lines.filtered(lambda x: x.name == tax_id.name).mapped('credit'))

        value_dict['sale_reverse_charge_taxable_amount'] = sale_reverse_charge_taxable_amount
        value_dict['sale_reverse_charge'] = sale_reverse_charge
        for tax_id in purchase_taxes:
            purchase_reverse_charge_taxable_amount += sum(
                account_move_lines.filtered(lambda x: x.name == tax_id.name).mapped('move_id.amount_untaxed'))
            purchase_reverse_charge += sum(account_move_lines.filtered(lambda x: x.name == tax_id.name).mapped('debit'))
        value_dict['purchase_reverse_charge'] = purchase_reverse_charge
        value_dict['purchase_reverse_charge_taxable_amount'] = purchase_reverse_charge_taxable_amount
        if group_local_purchase["taxes"]:
            value_dict['purchase'].append(group_local_purchase)

        if group_gcc_purchase["taxes"]:
            value_dict['purchase'].append(group_gcc_purchase)

        if group_outside_gcc_purchase["taxes"]:
            value_dict['purchase'].append(group_outside_gcc_purchase)

        if group_captial_goods["taxes"]:
            value_dict['purchase'].append(group_captial_goods)
        value_list.append(value_dict)
        return value_list

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        sheet = workbook.add_worksheet('Vat Return Report')
        heading = workbook.add_format({'bold': True, 'font_size': 14})
        sub_heading = workbook.add_format({'bold': True, 'font_size': 12})
        align = workbook.add_format({'font_size': 10})
        particular_head_align = workbook.add_format(
            {'border': 1, 'top': 1, 'bottom': 1, 'left': 0, 'right': 0, 'font_size': 10, 'bold': True,
             'align': 'center'})
        voucher_head_align = workbook.add_format(
            {'border': 1, 'top': 1, 'bottom': 1, 'left': 0, 'right': 0, 'font_size': 10, 'bold': True,
             'align': 'right'})
        sub_head = workbook.add_format(
            {'font_size': 10, 'bold': True, 'align': 'left'})
        sub_head_value = workbook.add_format(
            {'font_size': 10, 'bold': True, 'align': 'right'})
        sub_first_head = workbook.add_format(
            {'font_size': 10, 'align': 'left'})
        sub_first_head_value = workbook.add_format(
            {'font_size': 10, 'align': 'right'})
        sale_head_align = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'border': 1, 'top': 0, 'left': 0, 'right': 0, 'bold': 1})
        payment_details = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'border': 1, 'left': 0, 'right': 0, 'bold': 1})
        company_id = self.env['res.company'].sudo().search([], order='id ASC')
        if self.company_id:
            company_id = self.company_id
        col = 0
        sheet.set_row(0, 20)
        sheet.set_row(1, 20)

        for company in company_id:
            row = 0
            sheet.set_column(col, col, 5)
            sheet.set_column(col + 1, col + 1, 20)
            sheet.set_column(col + 2, col + 2, 20)
            sheet.set_column(col + 3, col + 3, 15)
            # sheet.set_column(col+3, col+3, 15)

            lines = self.get_values(company)
            sheet.merge_range(row, col, row, col + 5, company.name, heading)
            sheet.merge_range(row + 1, col, row + 1, col + 5, 'VAT Return', sub_heading)
            sheet.merge_range(row + 2, col, row + 2, col + 5,
                              '%s to %s' % (self.date_from.strftime("%d-%b-%Y"), self.date_to.strftime("%d-%b-%Y")),
                              align)
            sheet.merge_range(row + 3, col, row + 3, col + 2, 'Particulars', particular_head_align)
            sheet.merge_range(row + 3, col + 3, row + 3, col + 5, 'Voucher Count', voucher_head_align)
            domain = [('move_type', 'in', ['in_invoice', 'out_invoice']), ('company_id', '=', company.id),
                      ('invoice_date', '>=', self.date_from), ('invoice_date', '<=', self.date_to)]
            if self.target_moves == 'all_posted_entries':
                domain.append(('parent_state', '=', 'posted'))
            include_return_line = self.env['account.move'].search([
                ('move_type', 'in', ['in_invoice', 'out_invoice'])

            ])
            tax_adjustment_return_line = self.env['account.move'].search_count(
                [('move_type', 'in', ['entry']), ('company_id', '=', company.id),
                 ('date', '>=', self.date_from), ('date', '<=', self.date_to),
                 ('journal_id', '=', self.env.ref('kg_mashirah_oil_accounting.tax_adjustment_journal').id)

                 ])
            include_return = 0
            not_relevant_return = 0
            tax_adjustment = 0
            total_count = 0
            for rec in include_return_line.invoice_line_ids:
                if rec.tax_ids:
                    for rec_line in rec.tax_ids:
                        if rec_line.amount > 0:
                            include_return += 1
                        if rec_line.amount == 0:
                            not_relevant_return += 1
            if tax_adjustment_return_line:
                tax_adjustment = tax_adjustment_return_line

            total_count = include_return + not_relevant_return + tax_adjustment
            sheet.merge_range(row + 4, col, row + 4, col + 2, 'Total Vouchers', sub_head)
            sheet.merge_range(row + 4, col + 3, row + 4, col + 5, total_count, sub_head_value)
            sheet.merge_range(row + 5, col + 1, row + 5, col + 2, 'Included in Return', sub_first_head)
            sheet.merge_range(row + 5, col + 3, row + 5, col + 5, include_return, sub_first_head_value)
            sheet.merge_range(row + 6, col + 1, row + 6, col + 2, 'Not relevant for this Return', sub_first_head)
            sheet.merge_range(row + 6, col + 3, row + 6, col + 5, not_relevant_return, sub_first_head_value)
            sheet.merge_range(row + 7, col + 1, row + 7, col + 2, 'Uncertain Transactions (Corrections needed)',
                              sub_first_head)
            sheet.merge_range(row + 7, col + 3, row + 7, col + 5, tax_adjustment, sub_first_head_value)
            sheet.merge_range(row + 8, col + 0, row + 8, col + 2, 'Parties with invalid VATIN', sub_head)
            sheet.merge_range(row + 8, col + 3, row + 8, col + 5, '', sub_head_value)

            # sale

            sheet.merge_range(row + 9, col + 0, row + 9, col + 2, 'Particulars', particular_head_align)
            sheet.write(row + 9, col + 3, 'Taxable Amount', voucher_head_align)
            sheet.merge_range(row + 9, col + 4, row + 9, col + 5, 'Tax Amount', voucher_head_align)
            new_row = 10
            new_row1 = new_row
            total_sale = 0
            if lines[0]['sales']:
                sheet.merge_range(new_row, col, new_row, col + 2, 'Sales (Outwards) :', sale_head_align)
                sheet.write(new_row, col + 3, '', sub_head_value)
                sheet.merge_range(new_row, col + 4, new_row, col + 5, '', sub_head_value)
                for line in lines[0]['sales']:

                    sheet.merge_range(new_row + 1, col, new_row + 1, col + 2, line['group'], sub_head)
                    sheet.write(new_row + 1, col + 3, line['total_taxable'], sub_head_value)
                    sheet.merge_range(new_row + 1, col + 4, new_row + 1, col + 5, line['total_tax'], sub_head_value)
                    new_row += 2

                    for tax in line['taxes']:
                        sheet.merge_range(new_row, col + 1, new_row, col + 2, tax['name'], sub_first_head)
                        sheet.write(new_row, col + 3, tax['base_amount'], sub_first_head_value)
                        sheet.merge_range(new_row, col + 4, new_row, col + 5, tax['amount'], sub_first_head_value)
                        # total += tax['amount']
                        # row+=1
                        new_row += 1

                    # row+=1
                sale_reverse_taxable_amount = 0
                sale_reverse_tax_amount = 0
                if lines[0]['sale_reverse_charge']:
                    sale_reverse_tax_amount = lines[0]['sale_reverse_charge']
                if lines[0]['sale_reverse_charge_taxable_amount']:
                    sale_reverse_taxable_amount = lines[0]['sale_reverse_charge_taxable_amount']

                sheet.merge_range(new_row, col + 0, new_row, col + 2, 'Reverse Charge', sub_head)
                sheet.write(new_row, col + 3, sale_reverse_taxable_amount, sub_head_value)
                sheet.merge_range(new_row, col + 4, new_row, col + 5, sale_reverse_tax_amount, sub_head_value)
                sheet.merge_range(new_row + 1, col + 0, new_row + 1, col + 2, 'Total', sub_head)
                sheet.write(new_row + 1, col + 3, line['total_taxable'] + sale_reverse_taxable_amount,
                            voucher_head_align)
                sheet.merge_range(new_row + 1, col + 4, new_row + 1, col + 5,
                                  line['total_tax'] + sale_reverse_tax_amount,
                                  voucher_head_align)
                total_sale += line['total_tax'] + sale_reverse_tax_amount
                new_row1 = new_row + 2

            # purchase
            if lines[0]['purchase']:
                total_purchase_taxable = 0
                total_purchase_tax = 0
                sheet.merge_range(new_row1, col, new_row1, col + 2, 'Purchases (Inwards) :', sale_head_align)
                sheet.write(new_row1, col + 3, '', sub_head_value)
                sheet.merge_range(new_row1, col + 4, new_row1, col + 5, '', sub_head_value)
                sheet.merge_range(new_row1 + 1, col, new_row1 + 1, col + 2, 'Excess Input Credit Brought Forward',
                                  sub_first_head)
                sheet.write(new_row1 + 1, col + 3, '', sub_head_value)
                sheet.merge_range(new_row1 + 1, col + 4, new_row1 + 1, col + 5, '', sub_head_value)
                new_row1 = new_row1 + 2
                for line in lines[0]['purchase']:
                    sheet.merge_range(new_row1, col, new_row1, col + 2, line['group'], sub_head)
                    sheet.write(new_row1, col + 3, line['total_taxable'], sub_head_value)
                    sheet.merge_range(new_row1, col + 4, new_row1, col + 5, line['total_tax'], sub_head_value)
                    new_row1 += 1
                    for tax in line['taxes']:
                        sheet.merge_range(new_row1, col + 1, new_row1, col + 2, tax['name'], sub_first_head)
                        sheet.write(new_row1, col + 3, tax['base_amount'], sub_first_head_value)
                        sheet.merge_range(new_row1, col + 4, new_row1, col + 5, tax['amount'], sub_first_head_value)
                        total_purchase_taxable += tax['base_amount']
                        total_purchase_tax += tax['amount']
                        new_row1 += 1
                purchase_reverse_taxable_amount = 0
                purchase_reverse_tax_amount = 0
                if lines[0]['purchase_reverse_charge']:
                    purchase_reverse_tax_amount = lines[0]['purchase_reverse_charge']
                if lines[0]['purchase_reverse_charge_taxable_amount']:
                    purchase_reverse_taxable_amount = lines[0]['purchase_reverse_charge_taxable_amount']
                total_purchase_taxable += purchase_reverse_taxable_amount
                total_purchase_tax += purchase_reverse_tax_amount
                sheet.merge_range(new_row1, col + 0, new_row1, col + 2, 'Reverse Charge', sub_head)
                sheet.write(new_row1, col + 3, purchase_reverse_taxable_amount, sub_head_value)
                sheet.merge_range(new_row1, col + 4, new_row1, col + 5, purchase_reverse_tax_amount, sub_head_value)

                adjust_domain = [('company_id', '=', company.id), ('date', '>=', self.date_from),
                                 ('date', '<=', self.date_to), ('journal_id', '=', self.env.ref(
                        'kg_mashirah_oil_accounting.tax_adjustment_journal').id)]
                if self.target_moves == 'all_posted_entries':
                    adjust_domain.append(('state', '=', 'posted'))
                adjustment_line = sum(self.env['account.move'].sudo().search(adjust_domain).mapped('amount_total'))
                sheet.merge_range(new_row1 + 1, col + 0, new_row1 + 1, col + 2, 'Adjustments for input', sub_head)
                sheet.write(new_row1 + 1, col + 3, '', sub_head_value)
                sheet.merge_range(new_row1 + 1, col + 4, new_row1 + 1, col + 5, adjustment_line, sub_head_value)

                sheet.merge_range(new_row1 + 2, col + 0, new_row1 + 2, col + 2, 'Total', sub_head)
                sheet.write(new_row1 + 2, col + 3, total_purchase_taxable, voucher_head_align)
                refund = 0
                if (total_purchase_tax and total_sale) and total_purchase_tax > total_sale:
                    refund = total_sale - total_purchase_tax
                sheet.merge_range(new_row1 + 2, col + 4, new_row1 + 2, col + 5, total_purchase_tax, voucher_head_align)
                sheet.merge_range(new_row1 + 3, col + 0, new_row1 + 3, col + 2, 'Refundable', sub_head)
                sheet.write(new_row1 + 3, col + 3, '', voucher_head_align)
                sheet.merge_range(new_row1 + 3, col + 4, new_row1 + 3, col + 5, refund, voucher_head_align)
                new_row1 = new_row1 + 4

            sheet.merge_range(new_row1, col + 0, new_row1, col + 2, 'Payment Details', payment_details)
            sheet.merge_range(new_row1, col + 3, new_row1, col + 5,
                              '%s to %s' % (self.date_from.strftime("%d-%b-%Y"), self.date_to.strftime("%d-%b-%Y")),
                              voucher_head_align)
            sheet.merge_range(new_row1 + 1, col + 0, new_row1 + 1, col + 2, 'Tax payment (included)', sub_first_head)
            sheet.write(new_row1 + 1, col + 3, '', sub_first_head_value)
            sheet.merge_range(new_row1 + 1, col + 4, new_row1 + 1, col + 5, '', sub_first_head_value)
            sheet.merge_range(new_row1 + 2, col + 0, new_row1 + 2, col + 2, 'Tax payments (not included/uncertain)',
                              sub_first_head)
            sheet.write(new_row1 + 2, col + 3, '', sub_first_head_value)
            sheet.merge_range(new_row1 + 2, col + 4, new_row1 + 2, col + 5, '', sub_first_head_value)
            sheet.merge_range(new_row1 + 3, col + 0, new_row1 + 3, col + 2, 'Tax paid at customs', sub_first_head)
            sheet.write(new_row1 + 3, col + 3, '', sub_first_head_value)
            sheet.merge_range(new_row1 + 3, col + 4, new_row1 + 3, col + 5, '', sub_first_head_value)

            sheet.merge_range(new_row1 + 4, col + 0, new_row1 + 4, col + 2, 'VAT Paid', payment_details)
            sheet.write(new_row1 + 4, col + 3, '', voucher_head_align)
            sheet.merge_range(new_row1 + 4, col + 4, new_row1 + 4, col + 5, '', voucher_head_align)
            sheet.merge_range(new_row1 + 5, col + 0, new_row1 + 5, col + 2, 'Total VAT Refundable', sub_head)
            sheet.merge_range(new_row1 + 5, col + 3, new_row1 + 5, col + 5, '', sub_head_value)
            sheet.merge_range(new_row1 + 6, col + 0, new_row1 + 6, col + 2, 'Refund Claimed', sub_head)
            sheet.merge_range(new_row1 + 6, col + 3, new_row1 + 6, col + 5, '', sub_head_value)

            col += 8

    def xlsx_print(self):
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {

            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'Vat Return Report'
        filename = '%s_%s' % (report_name, datetime_string)
        self.write({'fileout': fout, 'fileout_filename': filename})
        file_io.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

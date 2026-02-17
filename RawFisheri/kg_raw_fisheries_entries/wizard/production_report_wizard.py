# -*- coding: utf-8 -*-
from datetime import datetime
from base64 import encodebytes
from io import BytesIO

import xlsxwriter

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ProductionReportWizard(models.TransientModel):
    _name = 'production.report.wizard'
    _description = 'production.report.wizard'

    date_from = fields.Date(string='Date From', default=fields.Date.context_today)
    date_to = fields.Date(string='Date To', default=fields.Date.context_today)
    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel")
    batch_id = fields.Many2one("stock.batch", string="Batch")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def action_print_xlsx(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))

        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {

            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_modelsalary.reportl': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        report_name = 'Frozen Stock Report'
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        sheet = workbook.add_worksheet('Frozen Stock Report')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 2, 10)
        sheet.set_column(3, 3, 10)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)

        right_no_color = workbook.add_format({'bold': True, 'align': 'right', 'border': 1})
        center_no_color = workbook.add_format({'bold': True, 'align': 'center', 'border': 1, 'num_format': '0.00'})
        percent_center_no_color = workbook.add_format(
            {'bold': True, 'align': 'center', 'border': 1, 'num_format': '0.00 %'})
        center_blue_color = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#4db8ff', 'border': 1})
        left_blue_color = workbook.add_format({'bold': True, 'align': 'left', 'bg_color': '#4db8ff', 'border': 1})
        center_orange_color = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#ffb84d', 'border': 1})

        row = 0
        col = 1

        row = row + 1
        col = col

        date_from = datetime.strptime(str(self.date_from), '%Y-%m-%d').strftime('%-d %b %y')
        date_to = datetime.strptime(str(self.date_to), '%Y-%m-%d').strftime('%-d %b %y')
        date_str = str(date_from) + ' - ' + str(date_to)

        domain = [('state', '=', 'updated'), ('date', '>=', self.date_from), ('date', '<=', self.date_to),
                  ('product_id.is_fish', '=', True)]
        if self.vessel_id:
            domain.append(('vessel_id', '=', self.vessel_id.id))
        if self.batch_id:
            domain.append(('batch_id', '=', self.batch_id.id))

        frozen_prod_entries = self.env['inventory.update'].search(domain)

        frozen_today = False
        if frozen_prod_entries:
            frozen_today = sum(frozen_prod_entries.mapped('kg'))

        total_kg_onboard = 0.00
        products = self.env['product.template'].search([('is_fish', '=', True)])
        for prd in products:
            total_kg_onboard += prd.qty_available * prd.uom_id.factor_inv
        total_on_board = total_kg_onboard

        sheet.write(row, col, 'Date', right_no_color)
        sheet.merge_range(row, col + 2, row, col + 1, date_str, center_no_color)
        sheet.write(row, col + 3, 'Frozen Today', center_blue_color)
        sheet.write(row, col + 4, frozen_today if frozen_today else '', center_no_color)
        sheet.write(row, col + 5, 'Total on Board', center_orange_color)
        sheet.write(row, col + 6, total_on_board if total_on_board else '', center_no_color)

        row = row + 1
        col = col

        sheet.merge_range(row, col, row + 1, col, 'Batch', right_no_color)
        sheet.merge_range(row, col + 1, row + 1, col + 2, self.batch_id.name if self.batch_id else '', center_no_color)
        sheet.merge_range(row, col + 3, row, col + 4, 'Today', center_blue_color)
        sheet.merge_range(row, col + 5, row, col + 6, 'On Stock', center_orange_color)

        row = row + 1
        col = col

        sheet.write(row, col + 3, 'Kg Today', center_blue_color)
        sheet.write(row, col + 4, '% Today', center_blue_color)
        sheet.write(row, col + 5, 'Kg on Board', center_orange_color)
        sheet.write(row, col + 6, '% on Board', center_orange_color)

        row = row + 1
        col = col

        for prod in products:
            domain = [('product_id', '=', prod.id), ('date', '>=', self.date_from), ('date', '<=', self.date_to),
                      ('state', '=', 'updated')]
            if self.vessel_id:
                domain.append(('vessel_id', '=', self.vessel_id.id))
            if self.batch_id:
                domain.append(('batch_id', '=', self.batch_id.id))
            prod_entries = self.env['inventory.update'].search(domain)

            today_qty = round(sum(prod_entries.mapped('kg')), 2)
            formatted_today_qty = f"{today_qty:.2f}"

            kg_onboard = prod.qty_available * prod.uom_id.factor_inv
            formatted_kg_onboard = f"{kg_onboard:.2f}"

            today_percentage = float(
                formatted_today_qty) / frozen_today if formatted_today_qty and frozen_today else 0.00
            onboard_percentage = float(
                formatted_kg_onboard) / total_on_board if formatted_kg_onboard and total_on_board else 0.00

            sheet.write(row, col, prod.name, left_blue_color)
            sheet.write(row, col + 1, prod.default_code if prod.default_code else '', center_blue_color)
            sheet.write(row, col + 2, prod.uom_id.name, center_blue_color)
            sheet.write(row, col + 3, float(formatted_today_qty) if formatted_today_qty else 0.00, center_no_color)
            sheet.write(row, col + 4, today_percentage, percent_center_no_color)
            sheet.write(row, col + 5, float(formatted_kg_onboard) if formatted_kg_onboard else 0.00, center_no_color)
            sheet.write(row, col + 6, onboard_percentage, percent_center_no_color)

            row = row + 1
            col = col

        # warehouse_data = self.get_data()

        # enteries = inventory_update_ids.filtered(
        #     lambda
        #         x: x.date and x.date >= self.date_from and x.date <= self.date_to and x.state == 'updated' and x.product_id.is_fish)

        # product_ids = set(enteries.mapped('product_id').ids) | set(self.env['product.template'].search(
        #     [('name', 'in', list(warehouse_data.keys())), ('is_fish', '=', True)]).ids)
        #
        # products = self.env['product.template'].browse(product_ids)
        #
        # update_map = {u.product_id.id: u for u in enteries}
        # if enteries:
        #     for entry in enteries:
        # update = update_map.get(product.id)
        # code = product.default_code or ''
        # box_size = update.uom_id.name if update and update.uom_id else product.uom_id.name
        # today_qty = update.kg if update else 0
        # on_board_kg = warehouse_data.get(product.name, {}).get('kg', 0)
        #
        # percent_today = today_qty / frozen_today if frozen_today else 0
        # percent_on_board = on_board_kg / total_on_board if total_on_board else 0

        # sheet.write(row, col, entry.product_id.name, left_blue_color)
        # sheet.write(row, col + 1, entry.name, center_blue_color)
        # sheet.write(row, col + 2, entry.uom_id.name, center_blue_color)
        # sheet.write(row, col + 3, today_qty, center_no_color)
        # sheet.write(row, col + 4, percent_today, center_no_color)
        # sheet.write(row, col + 5, on_board_kg, center_no_color)
        # sheet.write(row, col + 6, percent_on_board, center_no_color)
        #
        # row = row + 1
        # col = col

    # def get_data(self):
    #     products = self.env['product.template'].search([('is_fish', '=', True)])
    #
    #     domain = []
    #     if self.vessel_id:
    #         domain.append(('vessel_id', '=', self.vessel_id.id))
    #     if self.batch_id:
    #         domain.append(('batch_id', '=', self.batch_id.id))
    #
    #     warehouse_data = {}
    #
    #     if domain:
    #         for product in products:
    #             domain.append(('product_id.product_tmpl_id', '=', product.id))
    #             quants = self.env['stock.quant'].search(domain)
    #             total_qty = sum(quants.mapped('quantity'))
    #             uom_factor = product.uom_id.factor_inv
    #             warehouse_data[product.name] = {
    #                 'qty': total_qty,
    #                 'uom_factor': uom_factor,
    #                 'kg': total_qty * uom_factor
    #             }
    #
    #     return warehouse_data

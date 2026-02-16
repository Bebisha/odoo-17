# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal
import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class CustomerPortal(portal.CustomerPortal):
    """This class inherits controller portal"""

    def _prepare_home_portal_values(self, counters):
        """This function super the method and set count as none
        :param int counters: count of the product
        :param auth: The user must be authenticated and the current
        request will perform using the rights that the user was given.
        :param string type: HTTP Request and JSON Request,utilizing HTTP
        requests via the GET and POST methods. HTTP methods such as GET, POST,
        PUT, DELETE
        :return: values in counters
       """
        values = super()._prepare_home_portal_values(counters)
        if 's_count' in counters:
            values['s_count'] = None
        return values

    @http.route('/my/pro', type='http', auth="user", website=True)
    def portal_stock_products(self, **kw):
        """Adding stock check option in portal"""
        return request.render("kg_portal_stock_move.portal_stock_product_availability")

    @http.route('/product/search/move', type='json', auth="user", website=True)
    def search_product_stock(self, args):
        """To get corresponding products matching domain conditions
        :param args: Name input on search product
        :return: Result of input text given for searching the product
        """
        product = args['product']
        from_date = args.get('from_date')
        to_date = args.get('to_date')
        if product:
            user_warehouse_id = request.env.user.property_warehouse_id.id if request.env.user.property_warehouse_id else False
            domain = [('product_id.name', 'ilike', product),
                      ('warehouse_ids', 'in', request.env.user.property_warehouse_id.id)]
            if user_warehouse_id:
                domain.append(('warehouse_ids', 'in', user_warehouse_id))

            if from_date and to_date:
                domain += [('date', '>=', from_date), ('date', '<=', to_date)]
            domain += []
            res = request.env['stock.move.line'].sudo().search_read(
                domain=domain,
                fields=['id', 'date', 'reference', 'product_id', 'lot_id', 'location_id', 'location_dest_id',
                        'quantity', 'product_uom_id', 'state'])
            return res
        return False

    @http.route('/stock/download/move', type='http', auth="user", website=True)
    def download_stock_move(self, **kw):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '12px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        date_style = workbook.add_format(
            {'text_wrap': True, 'font_size': '10px', 'num_format': 'dd-mm-yyyy', 'align': 'left'})

        amt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        bold = workbook.add_format({'bold': True, 'font_size': '10px', 'align': 'center'})
        sheet.set_column(1, 3, 20)
        sheet.merge_range('A1:B1', 'Stock Move Report', head)
        sheet.merge_range('A3:B3', 'References', bold)
        sheet.merge_range('C3:D3', 'Product', bold)
        sheet.merge_range('E3:F3', 'Lot/serial No.', bold)
        sheet.merge_range('G3:I3', 'Location From', bold)
        sheet.merge_range('J3:L3', 'Location To', bold)
        sheet.write('M3', 'Qty', bold)
        sheet.write('N3', 'Unit', bold)
        sheet.write('O3', 'Status', bold)
        product = kw.get('products_search_move')
        from_date = kw.get('from_date')
        to_date = kw.get('to_date')
        domain = [('warehouse_ids', 'in', request.env.user.property_warehouse_id.id)]
        if product:
            domain += [('product_id.name', 'ilike', product)]
        if from_date and to_date:
            domain += [('date', '>=', from_date), ('date', '<=', to_date)]
        res = request.env['stock.move.line'].sudo().search_read(
            domain=domain,
            fields=['id', 'date', 'reference', 'product_id', 'lot_id', 'location_id', 'location_dest_id',
                    'quantity', 'product_uom_id', 'state'])
        row = 4
        for product in res:
            sheet.merge_range('A' + str(row) + ':B' + str(row), product['reference'], amt)
            sheet.merge_range('C' + str(row) + ':D' + str(row), product['product_id'][1], amt)
            sheet.merge_range('E' + str(row) + ':F' + str(row), product['lot_id'][1] if product['lot_id'] else '', amt)
            sheet.merge_range('G' + str(row) + ':I' + str(row),
                              product['location_id'][1] if product['location_id'] else '', amt)
            sheet.merge_range('J' + str(row) + ':L' + str(row),
                              product['location_dest_id'][1] if product['location_dest_id'] else '', amt)
            sheet.write('M' + str(row), product['quantity'], amt)
            sheet.write('N' + str(row), product['product_uom_id'][1] if product['product_uom_id'] else '', amt)
            sheet.write('O' + str(row), product['state'], amt)
            row += 1
        workbook.close()
        output.seek(0)
        return http.send_file(output, filename='stock_move.xlsx', as_attachment=True)

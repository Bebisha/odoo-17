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
        if 'p_count' in counters:
            values['p_count'] = None
        return values

    @http.route('/my/products', type='http', auth="user", website=True)
    def portal_products(self, **kw):
        """Adding stock check option in portal"""
        return request.render("kg_portal_stock_report.portal_product_availability")

    @http.route('/product/search', type='json', auth="user", website=True)
    def search_product(self, args):
        print(args, "dfhzhhhhhhhhhhhh")
        """To get corresponding products matching domain conditions
        :param args: Name input on search product
        :return: Result of input text given for searching the product
        """
        product = args['product']

        if product:
            # user_warehouse = request.env.user.sudo().warehouse_id
            user_warehouse_id = request.env.user.property_warehouse_id.id if request.env.user.property_warehouse_id else False
            domain = [('name', 'ilike', product), ('is_published', '=', True)]

            if user_warehouse_id:
                domain.append(('warehouse_ids', 'in', user_warehouse_id))

            res = request.env['product.product'].sudo().search_read(
                domain=domain,
                fields=['id', 'display_name', 'qty_available', 'virtual_available', 'free_qty', 'incoming_qty',
                        'outgoing_qty'])
            # pdf = request.env['report'].sudo().get_pdf([product], 'module_name.report_name', data=None)
            # pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return res
        return False

    @http.route('/stock/download/print', type='http', auth="user", website=True)
    def download_excel(self, **kw):
        print("Download File")
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '13px'})

        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})

        date_style = workbook.add_format(
            {'text_wrap': True, 'font_size': '10px', 'num_format': 'dd-mm-yyyy', 'align': 'left'})

        amt = workbook.add_format({'font_size': '10px', 'align': 'center'})

        bold = workbook.add_format({'bold': True, 'font_size': '8px', 'align': 'center'})

        sheet.set_column(1, 3, 20)

        sheet.write('A1', 'Stock Report', txt)
        sheet.write('A3', 'Product', txt)
        sheet.write('D3', 'Quantity', txt)
        # sheet.write('F3', 'Free to use',txt)
        sheet.write('H3', 'Incoming(Transit)', txt)
        sheet.write('J3', 'Outgoing(Transit)', txt)

        products_search = kw.get('products_search')
        user_warehouse_id = request.env.user.property_warehouse_id.id if request.env.user.property_warehouse_id else False

        # Modify the query based on search parameters and user's warehouse
        if products_search:
            if user_warehouse_id:
                domain = [('name', 'ilike', products_search), ('warehouse_ids', 'in', user_warehouse_id),
                          ('is_published', '=', True)]
            else:
                domain = [('name', 'ilike', products_search), ('is_published', '=', True)]
        else:
            if user_warehouse_id:
                domain = [('warehouse_ids', 'in', user_warehouse_id), ('is_published', '=', True)]
            else:
                domain = [('is_published', '=', True)]

        # domain = [('is_published', '=', True),('warehouse_ids', 'in', request.env.user.property_warehouse_id.id)]
        res = request.env['product.product'].sudo().search_read(
            domain=domain,
            fields=['display_name', 'qty_available', 'free_qty', 'incoming_qty',
                    'outgoing_qty'])
        print(res, "fdfdfdfdfddd")

        row = 4
        for product in res:
            sheet.write(row, 0, product['display_name'])
            sheet.write(row, 3, product['qty_available'], amt)
            # sheet.write(row, 5, product['free_qty'], amt)
            sheet.write(row, 7, product['incoming_qty'], amt)
            sheet.write(row, 9, product['outgoing_qty'], amt)
            row += 1

        workbook.close()

        output.seek(0)

        return http.send_file(output, filename='stock_report.xlsx', as_attachment=True)



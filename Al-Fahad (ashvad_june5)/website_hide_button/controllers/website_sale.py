# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil Ashok (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):
    """class to hide price, add to cart and quantity"""

    # @http.route([
    #     '''/shop''',
    #     '''/shop/page/<int:page>''',
    #     '''/shop/category/<model("product.public.category"):category>''',
    #     '''/shop/category/<model("product.public.category"):category>/
    #     page/<int:page>'''
    # ], type='http', auth="public", website=True)
    # def shop(self, page=0, category=None, search='', min_price=0.0,
    #          max_price=0.0, ppg=False, **post):
    #     """Method for finding log in user or not in shop page """
    #     res = super().shop(page=0, category=None, search='', min_price=0.0,
    #                        max_price=0.0, ppg=False, **post)
    #     res.qcontext.update({
    #         'login_user': False if request.session.uid is None else True
    #     })
    #     return res

    def _prepare_product_values(self, product, category, search, **kwargs):
        """Method for finding log in user or not in product page """
        res = super(WebsiteSaleInherit, self)._prepare_product_values(product,
                                                                      category,
                                                                      search,
                                                                      **kwargs)
        res['login_user'] = False if request.session.uid is None else True
        return res

    @http.route()
    def shop_payment(self, **post):
        """  Restrict public visitors from accessing payment page so that SO
        creation will be disabled   """
        user = http.request.env.user
        if user and user.has_group('base.group_portal') or \
                user.has_group('base.group_user'):
            res = super(WebsiteSaleInherit, self).shop_payment(**post)
            return res
        return request.redirect("/")


class ProductEnquiry(http.Controller):

    @http.route('/shop/product_enquiry/<model("product.template"):product>', type='http', auth="public", website=True)
    def product_enquiry(self, product, **kwargs):
        values = {
            'product': product,
        }
        return request.render("website_hide_button.product_enquiry_form", values)

    @http.route('/shop/product_enquiry/submit', type='http', auth="public", methods=['POST'], website=True)
    def product_enquiry_submit(self, **kwargs):
        """ Sending email for product enquiry """
        product_id, name, email, phone, message = map(kwargs.get, ['product_id', 'name', 'email', 'phone', 'message'])
        product = request.env['product.template'].sudo().browse(int(product_id))
        enquiry = request.env['product.enquiry'].sudo().create({
            'product_id': product.id,
            'name': name,
            'email': email,
            'phone': phone,
            'message': message,
        })
        if enquiry:
            message_body = (f'<p>Dear Admin,<br><br>You have received a new product enquiry: <br><br>'
                            f'<b>Product :</b> {enquiry.product_id.name} <br><br>'
                            f'<b>Name : </b>{enquiry.name} <br><br><b>Email : </b>{enquiry.email} <br><br>'
                            f'<b>Message : </b>{enquiry.message}</p>')
            mail_values = {
                'subject': f'New Product Enquiry from {enquiry.name}',
                'body_html': message_body,
                # 'email_from': request.env.user.partner_id.email,
                'email_to': request.env.company.email,
                'model': 'product.enquiry',
                'res_id': enquiry.id,
            }
            request.env['mail.mail'].sudo().create(mail_values).send()
        return request.redirect('/shop/product_enquiry/thanks')

    @http.route('/shop/product_enquiry/thanks', type='http', auth="public", website=True)
    def product_enquiry_thanks(self, **kwargs):
        return request.render('website_hide_button.product_enquiry_thanks')

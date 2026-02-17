from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo.http import request


class WebsitePortal(CustomerPortal):

    @http.route('/kg/portal/ai_menu/<string:country>', type='http', auth='public', website=True)
    def ai_form(self, country,**kwargs):
        if country == 'us':
            country = "us"
        else:
            country = "ae"
        return request.render('kg_itron_website.portal_ai_form', {
            'source_menu': 'AI',
            'country': country,
        })

    @http.route('/kg/portal/kiosks_menu/<string:country>', type='http', auth='public', website=True)
    def kiosk_form(self,country, **kwargs):
        if country == 'us':
            country = "us"
        else:
            country = "ae"
        return request.render('kg_itron_website.portal_kiosks_form',{
        'source_menu': 'Kiosk',
        'country': country,
    })

    @http.route('/kg/portal/odoo_menu/<string:country>', type='http', auth='public', website=True)
    def odoo_form(self,country, **kwargs):
        if country == 'us':
            country = "us"
        else:
            country = "ae"
        return request.render('kg_itron_website.portal_odoo_form',{
        'source_menu': 'Odoo',
        'country': country,
    })

    @http.route('/kg/portal/payment_menu/<string:country>', type='http', auth='public', website=True)
    def payment_form(self, country,**kwargs):
        if country == 'us':
            country = "us"
        else:
            country = "ae"
        return request.render('kg_itron_website.portal_payment_form',{
        'source_menu': 'Payment',
        'country': country,

    })

    @http.route('/kg/portal/seo_menu/<string:country>', type='http', auth='public', website=True)
    def seo_form(self,country, **kwargs):
        print(country)
        if country == 'us':
            country = "us"
        else:
            country = "ae"
        return request.render('kg_itron_website.portal_seo_form',{
        'source_menu': 'Seo',
        'country': country,
    })

    @http.route('/kg/portal/devops/<string:country>', type='http', auth='public', website=True)
    def devops_form(self,country, **kwargs):
        if country == 'us':
            country = "us"
        else:
            country = "ae"
        return request.render('kg_itron_website.portal_devops_form',{
        'source_menu': 'Devops',
        'country': country,
    })

    @http.route('/kg/portal/testing_menu/<string:country>', type='http', auth='public', website=True)
    def testing_form(self,country, **kwargs):
        if country == 'us':
            country = "us"
        else:
            country = "ae"
        return request.render('kg_itron_website.portal_testing_form',{
        'source_menu': 'Testing',
        'country': country,
    })

    @http.route('/kg/portal/contact_us/<string:country>', type='http', auth='public', website=True)
    def contact_form_us(self, country,**kwargs):
        if country == 'us':
            country = "us"
        else:
            country = "ae"
        return request.render('kg_itron_website.custom_contact_us_us',
                              {
                                  'country': country,
                              })



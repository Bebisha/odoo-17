# Copyright 2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Website Sale Checkout Skip Payment",
    "summary": "Skip payment for logged users in checkout process",
    "version": "17.0.1.1.0",
    "category": "Website",
'author': 'Klystron Global',
    'maintainer': 'Bebisha C P',
    'website': "https://www.klystronglobal.com/",
    "license": "LGPL-3",
    "depends": ["website_sale","sale_management"],
    "data": [
        "views/website_sale_skip_payment.xml",
        "views/website_sale_template.xml",
        "views/partner_view.xml",
        "views/res_config_settings_views.xml",
        "views/sale_order_views.xml",
        "views/email_template.xml",
    ],

}

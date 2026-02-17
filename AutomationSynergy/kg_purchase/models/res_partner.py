# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    vendor_sequence = fields.Char(string='Vendor Code')
    customer_sequence = fields.Char(string='Customer Code')
    hide_peppol_fields = fields.Char(string='Customer Code')

    is_vendor = fields.Boolean("Vendor", default=False)
    vendor_type_id = fields.Many2one(
        'res.vendor.type', string='Type of Vendor'
    )
    # type_of_vendor =fields.Selection(
    #     [('trader', 'Trader'),
    #      ('facility_provider', 'Facility Provider'),
    #      ('fork_service', 'Fork Lift Service'),
    #      ('it_service', 'IT Service Provider'),
    #      ('logistics_service', 'Logistics Service'),
    #      ('manpower_supplier', 'Manpower Supplier'),
    #      ('manufacturer', 'Manufacturer'),
    #      ('packing ', 'Packing '),
    #      ('service_provider ', 'Service Provider '),
    #      ('stationery_supplier ', 'Service Provider '),
    #      ],   string="Type Of Vendor")

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResPartner, self).create(vals_list)
        search_partner_mode = self.env.context.get('res_partner_search_mode')
        is_customer = search_partner_mode == 'customer'
        is_supplier = search_partner_mode == 'supplier'
        if is_supplier:
            res.is_vendor = True
            res.vendor_sequence = self.env['ir.sequence'].next_by_code('vendor.sequence') or _('New')
        if is_customer:
            res.customer_sequence = self.env['ir.sequence'].next_by_code('customer.sequence') or _('New')


        return res

    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        args = list(args or [])
        if name:
            args += ['|', ('name', operator, name), ('vendor_sequence', operator, name)]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

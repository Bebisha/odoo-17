# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api


class AppointmentType(models.Model):
    _name = 'appointment.type'
    _description = 'Appointment Type'

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active", default=True)
    length = fields.Float(string="Length")
    code = fields.Integer(string="Code")
    chargeable = fields.Boolean(string="Chargeable",
                                default=True)
    product_id = fields.Many2one("product.product",
                                 string="Price List")
    price = fields.Float(string="Price")
    service_type_id = fields.Many2one('service.type',
                                      string="Service Type")
    clinic_id = fields.Many2one('res.company', string="Clinic",
                                default=lambda self:
                                self.env.user.company_id.id)
    tdcc_appointment_type_id = fields.Integer(string="TDCC Ref.")

    @api.onchange('product_id')
    def changed_product_id(self):
        if not self.product_id:
            return 0.00
        self.price = self.product_id.lst_price or 0.0

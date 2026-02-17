# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import api, fields, models, _
# from odoo.exceptions import Warning, UserError


class WatchStores(models.Model):
    _name = 'watch.stores'

    name = fields.Char('Name',required=True)



class WatchModels(models.Model):
    _name = 'watch.models'

    name = fields.Char('Model')

    brand_id = fields.Many2one('kg.casio.brand','Brand')

    in_stock = fields.Boolean('In Stock')


class WatchCategory(models.Model):
    _name = 'watch.category'

    name = fields.Char('Category')



class BookingDetails(models.Model):
    _name = "booking.details"

    name = fields.Char('Name')

    customer = fields.Char('Customer')

    brand_id = fields.Many2one('kg.casio.brand','Brand')

    model_id = fields.Many2one('watch.models','Model')

    store_id = fields.Many2one('watch.stores','Store')

    mobile_no = fields.Char('Mobile No')

    email = fields.Char('Email')

    book_date = fields.Date('Date')

    accept_cond = fields.Boolean('Accept Conditions')

    @api.model
    def create(self, vals):
        vals['book_date'] = date.today()
        return super(BookingDetails, self).create(vals)


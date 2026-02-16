from odoo import fields, models, api
from odoo import api, fields, models
import requests
import logging
import base64

from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Inherited sale. order class to add a new field for attachments"""
    _inherit = 'sale.order'


    create_image_fr= fields.Binary(string="PDfffffffffffffff")
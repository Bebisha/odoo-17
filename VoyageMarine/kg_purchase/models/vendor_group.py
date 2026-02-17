from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class KGVendorGroup(models.Model):
    _name = 'vendor.group'

    name = fields.Char(string="Group Name")
    code = fields.Char(string="Code")
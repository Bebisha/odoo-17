from odoo import models, fields, api
from passlib.context import CryptContext


class ResUsers(models.Model):
    _inherit = "res.users"

    plain_password = fields.Char("Plain Password")
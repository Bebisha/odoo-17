from odoo import models, fields, api, _
from ast import literal_eval
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class KGAccountRegisterInherit(models.TransientModel):
    _inherit = "account.payment.register"

    show_smart_button = fields.Boolean(string='Show Smart Button', default=False)




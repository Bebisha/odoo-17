from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KGProductCategoryInherit(models.Model):
    _inherit = "product.category"

    is_calibration = fields.Boolean(string="Is Calibration")
    is_lsa = fields.Boolean(string="IS LSA")
    is_ffa = fields.Boolean(string="IS FFA")
    is_field_service = fields.Boolean(string="IS FIELD_SERVICE")
    is_navigation_communication = fields.Boolean(string="NAVIGATION &amp; COMMUNICATION")
    is_scope = fields.Boolean(string="IS Scope")
    scope_code = fields.Char(string=" Scope Code")
    active = fields.Boolean(default=True)

    # is_gas_detection = fields.Boolean(string='Gas Detection')
    # is_fire_detection = fields.Boolean(string='Fire Detection')
    # is_electrical = fields.Boolean(string='Electrical')
    # is_measuring_control = fields.Boolean(string='Measuring Control')
    # is_navigation = fields.Boolean(string='Navigation')
    # is_communication = fields.Boolean(string='Communication')
    # is_featured_marine = fields.Boolean(string='Featured Marine Product')
    # is_cables = fields.Boolean(string='Cables')
    # is_hardwares = fields.Boolean(string='Hardwares')
    # is_tools = fields.Boolean(string='Tools & Equipment')
    # is_consumables = fields.Boolean(string='Consumables')
    # is_health_safety = fields.Boolean(string='Health, Safety & Environment')

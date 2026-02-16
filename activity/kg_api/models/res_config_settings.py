from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    external_api_base_url = fields.Char(
        string='External API Base URL',
        config_parameter='external_api.base_url',
        help="Base URL of the external system, e.g., http://localhost:5000"
    )

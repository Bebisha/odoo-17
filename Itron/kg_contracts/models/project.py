from datetime import datetime

from odoo import fields, models, api
from odoo.exceptions import UserError


class Project(models.Model):
    _inherit = 'project.project'

    is_show = fields.Boolean('Show')
    contract_type = fields.Selection([('onsite', 'Onsite'), ('offshore', 'Offshore'), ('amc', 'Amc')],
                                     'Contract Type',
                                     default='onsite')

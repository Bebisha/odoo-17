
from odoo import models, fields, api, _

class KGStockMove(models.Model):
    _inherit = 'stock.move'

    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'),('ft','FT')
    ], string="Code")
    unit_price = fields.Float(string='Unit Price')
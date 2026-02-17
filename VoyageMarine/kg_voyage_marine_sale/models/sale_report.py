from odoo import fields, models

class SaleReports(models.Model):
    _inherit = "sale.report"

    type_id = fields.Selection([('local', 'Local'), ('meast', 'Middle east'), ('international', 'International'),
                                ('sisconcern', 'Sister Concern'), ('subcontracting', 'Subcontracting')],
                               default='sisconcern', string="Type", related='partner_id.po_type', store=True)
    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'), ('ft', 'FT')
    ], string="Code",store=True)

    division_id = fields.Many2one("kg.divisions", string="Division",store=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res.update({
            'type_id': 'partner.po_type',
            'division_id': 's.division_id',
            'code': 'l.code',
        })
        return res

    def _group_by_sale(self):
        group_by = super()._group_by_sale()
        group_by += """
               , partner.po_type
               , s.division_id
               , l.code
           """
        return group_by
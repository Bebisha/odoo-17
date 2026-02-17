from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    attention = fields.Char('ATTN.')
    hide_peppol_fields = fields.Char(string='Customer Code')
#
#
class KGAccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    has_abnormal_deferred_dates = fields.Char()

from odoo import api, fields, models, _

class AccountTags(models.Model):
    _inherit = 'account.account.tag'

    import_vat = fields.Boolean('Import Vat Tax Grid?')
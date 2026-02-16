from odoo import models, fields


class ResCompanyInherit(models.Model):
    _inherit = "res.company"

    bldg_no = fields.Char(string="Bldg.No")
    way_no = fields.Char(string="Way No")
    fax = fields.Char(string="Fax")


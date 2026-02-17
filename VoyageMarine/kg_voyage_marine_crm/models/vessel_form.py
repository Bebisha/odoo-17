from odoo import models, fields, api, _



class KgVesselCode(models.Model):
    _name = 'vessel.code'


    code = fields.Char(string="Code")
    name = fields.Char(string="Vessel",relate="job_vessel")
    imo_number = fields.Char(string="IMO number")

    @api.onchange('code')
    def _onchange_code_upper(self):
        if self.code:
            self.code = self.code.upper()

    @api.onchange('name')
    def _onchange_name_upper(self):
        if self.name:
            self.name = self.name.upper()

    @api.model
    def create(self, vals):
        if 'code' in vals and vals['code']:
            vals['code'] = vals['code'].upper()
        if 'name' in vals and vals['name']:
            vals['name'] = vals['name'].upper()
        return super(KgVesselCode, self).create(vals)

    def write(self, vals):
        if 'code' in vals and vals['code']:
            vals['code'] = vals['code'].upper()
        if 'name' in vals and vals['name']:
            vals['name'] = vals['name'].upper()
        return super(KgVesselCode, self).write(vals)



class KGPickingInherit(models.Model):
    _inherit = "stock.picking"

    vessel_id = fields.Many2one('vessel.code', string='Vessel')

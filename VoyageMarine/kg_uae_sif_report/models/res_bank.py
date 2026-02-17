from odoo import models, fields, api

class Bank(models.Model):
    _inherit = 'res.bank'

    routing_code = fields.Char(string="Routing Code", size=9, required=True, help="Bank Route Code")

    def write(self, vals):
        if 'routing_code' in vals.keys():
            vals['routing_code'] = vals['routing_code'].zfill(9)
        return super(Bank, self).write(vals)

    @api.model
    def create(self, vals):
        if 'routing_code' in vals.keys():
            vals['routing_code'] = vals['routing_code'].zfill(9)
        return super(Bank, self).create(vals)
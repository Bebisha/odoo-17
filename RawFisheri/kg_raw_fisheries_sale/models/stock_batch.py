from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KGStockBatch(models.Model):
    _name = "stock.batch"
    _description = "Stock Batch"
    _inherit = ['mail.thread']

    name = fields.Char(string="Batch", required=True)

    @api.model_create_multi
    def create(self, vals):
        res = super(KGStockBatch, self).create(vals)
        if res.name:
            batch_id = self.search([('name', '=', res.name), ('id', '!=', res.id)])
            if batch_id:
                raise ValidationError("A batch with this name already exists !")
        return res

    def write(self, vals):
        res = super(KGStockBatch, self).write(vals)
        if vals.get('name'):
            batch_id = self.search([('name', '=', vals.get('name')), ('id', '!=', vals.get('id'))])
            if batch_id:
                raise ValidationError("A batch with this name already exists !")
        return res

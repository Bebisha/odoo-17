from odoo import models, fields, api, _



class KgDocumentsType(models.Model):
    _name = 'documents.type'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")

    def name_get(self):
        result = []

        for rec in self:
            if rec.code:
                result.append((rec.id, '[%s] %s' % (rec.code, rec.name)))
            else:
                result.append((rec.id, '%s' % (rec.name)))

        return result
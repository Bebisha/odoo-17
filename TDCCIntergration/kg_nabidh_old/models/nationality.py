from odoo import models, fields, api, _



class KgNationality(models.Model):
    _name = 'nationality.form'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")
    demo = fields.Char(string="demo")

    def name_get(self):
        demo = []

        for rec in self:
            if rec.code:
                demo.append((rec.id, '[%s] %s' % (rec.code, rec.name)))
            else:
                demo.append((rec.id, '%s' % (rec.name)))

        return demo
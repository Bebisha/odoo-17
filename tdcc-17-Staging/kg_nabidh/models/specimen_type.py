from odoo import models, fields, api, _



class KgSpecimenType(models.Model):
    _name = 'specimen.type'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")

class KgSpecimensource(models.Model):
    _name = 'specimen.source'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")


class KgSpecimencondition(models.Model):
    _name = 'specimen.condition'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")

class Kgspecimenspecimen(models.Model):
    _name = 'specimen.specimen'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")


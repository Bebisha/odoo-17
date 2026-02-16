from odoo import models, fields, api, _



class KgAdmitSource(models.Model):
    _name = 'admit.source'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")


class Kgbednumber(models.Model):
    _name = 'bed.number'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")

class ProblemStatus(models.Model):
    _name = 'problem.status'

    name = fields.Char(string="Description")
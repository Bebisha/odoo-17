from odoo import models, fields, api, _



class KgProblemLifeCycleStatus(models.Model):
    _name = 'life.cycle.status'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")


class KgProblemProblem(models.Model):
    _name = 'problem.problem'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")


class Kglocalcode(models.Model):
    _name = 'local.code'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")

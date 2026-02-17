from odoo import models, fields


class KGTypeSensors(models.Model):
    _name = "type.sensors"
    _description = "Type of Sensors"

    name = fields.Char(string="Name")


class KGTypeBody(models.Model):
    _name = "type.body"
    _description = "Type of Body"

    name = fields.Char(string="Name")


class KGTypeNetwork(models.Model):
    _name = "type.network"
    _description = "Type of Network"

    name = fields.Char(string="Name")


class KGTypeMounting(models.Model):
    _name = "type.mounting"
    _description = "Type of Mounting"

    name = fields.Char(string="Name")

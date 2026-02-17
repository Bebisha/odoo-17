from datetime import date

from odoo import models, fields, api


class KGSequenceWizard(models.TransientModel):
    _name = "sequence.lot"

    name = fields.Char(string="Sequence Number")

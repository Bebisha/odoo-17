import re

from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class KgSocialHabits(models.Model):
    _name= "social.habit"

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")


class KgSocialHabitsCategory(models.Model):
    _name = "social.habit.category"

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")

class KgSocialHabitsQty(models.Model):
    _name = "social.habit.qty"

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")

class KgsheryanId(models.Model):
    _name = "sheryan.id"


    name = fields.Char(string="ID" ,required=True, size=8)

    @api.constrains('name')
    def _check_field_length(self):
        for record in self:
            if record.name:
                if not record.name.isdigit() or len(record.name) != 8:
                    raise ValidationError("Your field must be exactly 8 digits long and contain only numbers.")
                if re.search(r'(\d)\1{3}', record.name):
                    raise ValidationError("Your Field must not contain 4 consecutive identical numbers.")
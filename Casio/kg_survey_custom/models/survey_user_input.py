from odoo import api, fields, models, tools


class Survey_UserInput(models.Model):
    _inherit = 'survey.user_input'

    mobile_no = fields.Char('Mobile No')

class Survey_UserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    mobile_no = fields.Char(related='user_input_id.mobile_no', store="1")
    email = fields.Char(related='user_input_id.email', store="1")

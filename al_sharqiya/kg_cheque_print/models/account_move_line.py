from odoo import models, fields


# class AccountMoveLIne(models.Model):
#     _inherit = 'account.move.line'
#
#     group_id = fields.Many2one('business.group', string="Group", related='partner_id.business_group_id')
#
#
# class AccountMove(models.Model):
#     _inherit = 'account.move'
#
#     business_group_id = fields.Many2one('business.group', string="Group", related='partner_id.business_group_id',
#                                         store=True)

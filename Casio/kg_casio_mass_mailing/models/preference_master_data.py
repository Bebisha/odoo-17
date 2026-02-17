from odoo import api, fields, models


class EmailPreferences(models.Model):
    _name = 'email.preferences'

    name = fields.Char(string='Frequency')


    # def action_get_partner(self):
    #     for rec in self:
    #         emp_id = self.env['res.partner'].search([('email', '=', rec.email)], limit=1)
    #         self.ensure_one()
    #         print('rr',emp_id)
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'name': 'Preference',
    #             'view_mode': 'kanban',
    #             'res_model': 'res.partner',
    #             'domain': [('id', '=', emp_id.id)],
    #             'context': "{'create': False}"
    #         }

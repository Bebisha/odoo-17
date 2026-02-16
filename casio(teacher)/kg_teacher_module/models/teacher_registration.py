from odoo import models, fields,api


class KGTeacherRegistration(models.Model):
    _name = 'teacher.registration'
    _description = 'Teacher Registration Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Name')
    email = fields.Char(string='Email')
    name_of_school = fields.Char(string='Name Of School')
    emulator_licence = fields.Char(string='Emulator License')
    emulator_licence_type = fields.Char(string='Emulator Licence Type')
    emul_licence_id= fields.Many2one('emulator.licence',string='Emulator Licence')
    end_date_emulator_licence = fields.Date(string="End Date")
    allocated_licenses = fields.One2many(
        'emulator.licence',
        'allocated_teachers',
        string='Allocated Licenses'
    )

    # @api.model
    def action_show_allocated_licenses(self, context=None):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Allocated Licenses',
            'res_model': 'emulator.licence',
            'domain': [('allocated_teachers', '=', self.id)],
            'view_type': 'tree',
            'view_mode': 'tree',
            'target': 'current',
        }


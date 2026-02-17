from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _


class MergeConfirmationWizard(models.Model):
    _name = 'merge.confirmation.wizard'
    _description = 'Merge Confirmation Wizard'

    student_id = fields.Many2one('res.partner', string='Student')

    def action_merge_patient(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'base.partner.merge.automatic.wizard',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Merge Patient',
            'context': {'default_patient_id': self.student_id.id,}
        }


    def create_appointment(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'appointment.appointment',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Appointment',
            'context': {'default_client_id': self.student_id.id}
        }



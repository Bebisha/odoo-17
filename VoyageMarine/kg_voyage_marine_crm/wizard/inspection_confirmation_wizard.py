from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _



class InspectionConfirmationWizard(models.TransientModel):
    _name = 'inspection.confirmation.wizard'
    _description = 'Inspection Confirmation Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead')

    def confirm(self):
        # Call the create_estimation logic from lead
        if self.lead_id:
            self.lead_id.force_create_estimation()
        return {'type': 'ir.actions.act_window_close'}



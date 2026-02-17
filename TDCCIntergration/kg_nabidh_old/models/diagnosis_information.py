from odoo import fields, models, api,_


class KgDiagnosisInformation(models.Model):
    _name = "diagnosis.information"


    diag_code = fields.Char(string="Diagnosis Code – DG1", help="J18.9^Pneumonia, unspecified organism^I10")
    diag_description = fields.Char(string="Diagnosis Description", help="Please provide the diagnosis description")
    diag_type = fields.Many2one('diagnosis.type',
                                 help="", string="Diagnosis Type")
    diag_priority = fields.Selection([('1',' Primary '),('2', ' Secondary')],string="Diagnosis Priority",
                                   help="The value 1 means that this is the primary diagnosis. Values 2-99 convey ranked secondary diagnoses")
    diag_action_code = fields.Selection([('A', 'Add'), ('D', 'Delete'), ('U', 'Update')],
                                        help="A means Add/Insert, D means Delete, and U means update",
                                        string="Diagnosis Action Code" )
    diagnosis_information_id = fields.Many2one('appointment.appointment', string='Student')
    diagnosis_coding_method = fields.Selection([('I10', 'ICD10'), ('SCT', 'SNOMED')], 'Diagnosis Coding Method',)
    set_id_dg1 = fields.Char(string='Set ID – DG1 ', copy=False, index=True, readonly=False,
                             default=lambda self: _('New'))
    dg1_date = fields.Datetime('Diagnosis Date Time', default=lambda self: fields.Datetime.now())

    @api.model
    def create(self, vals):
        if vals.get('set_id_dg1', _('New')) == _('New'):
            vals['set_id_dg1'] = self.env['ir.sequence'].next_by_code(
                'set_id_dg1') or _('New')
        return super(KgDiagnosisInformation, self).create(vals)
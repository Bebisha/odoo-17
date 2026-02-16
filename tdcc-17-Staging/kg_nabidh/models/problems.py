from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class KgProblems(models.Model):
    _name= "problems.form"

    name = fields.Char(string="Action Code")
    action_date_time = fields.Datetime(string="Action Date/Time")
    problem_established_date = fields.Datetime(string="Problem Established Date/Time")
    Problem_life_cycle_date = fields.Datetime(string="Problem Life Cycle Status Date/Time")
    Problem_onset_date = fields.Datetime(string="Problem Date of Onset")
    problem_classification = fields.Char(string="Problem Classification")

    problem_des_id= fields.Many2one('problem.problem',string="Problem ID")
    problem_id_code = fields.Char(related='problem_des_id.code', string="Problem ID")
    problem_id_name= fields.Char(string="Problem ID Name",deafult = "Prediabetes (disorder)" ,default="A90. Dengue fever (classical dengue)")
    activity_provider_code = fields.Char(string="Primary Activity ProviderCode", size=8)
    problems_form_id = fields.Many2one('appointment.appointment', string='Problems')
    life_cycle_status_id = fields.Many2one('life.cycle.status', string='Problem Life Cycle Status' ,default= lambda self: self.env['life.cycle.status'].search([('code', '=', '413322009')], limit=1))
    problem_id = fields.Selection([('I10', 'ICD10'), ('SCT', 'SNOMED')], 'Problem ID', )
    icdcode_id = fields.Selection([('I10', 'ICD10'), ('I09', 'I09')], 'ICDCode', default="I10")
    idc_code  = fields.Char(string="ICD Code" )
    local_code  = fields.Char(string="LocalCode")
    local_code_id  = fields.Many2one('local.code',string="LocalCode")
    snomed_code  = fields.Char(string="SNOMEDCode")
    status_id = fields.Many2one('problem.status',string='Problem Status')


    problem_life_cycle_status = fields.Selection([('Active', 'Active'), ('Inactive', 'Inactive'),('Chronic', 'Chronic'),('Intermittent', 'Intermittent'),('Recurrent', 'Recurrent'),('Suspected', 'Suspected'),('Ruled out', 'Ruled out'),('Resolved', 'Resolved')], 'Problem Life Cycle Status', )

    # @api.constrains('problem_id_code')
    # def _check_field_length(self):
    #     for record in self:
    #         if record.problem_id_code and len(record.problem_id_code) != 8:
    #             raise ValidationError("Problem ID must be exactly 8 characters long.")

class KgNotesComments(models.Model):
    _name= "notes.comments"

    set_id_nte = fields.Char(string='Set ID – NTE', readonly=False, default=lambda self: _('New'))

    note= fields.Text(string="Notes")
    source_comment= fields.Char(string="Source Of Comment")
    nte_id = fields.Many2one('appointment.appointment', string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('set_id_nte', _('New')) == _('New'):
            vals['set_id_nte'] = self.env['ir.sequence'].next_by_code(
                'set_id_nte') or _('New')
        res = super(KgNotesComments, self).create(vals)
        return res




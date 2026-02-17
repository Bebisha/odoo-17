from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'


    def action_send_survey(self):
        upt_qstn_lines = self.question_ids.filtered(lambda x: x.update_result)
        if upt_qstn_lines:
            name_or_email = upt_qstn_lines.mapped('contact_field_id.name')
            if 'name' not in name_or_email:
                raise ValidationError(_("'Name' question is mandatory for surveys that include contact update questions."))
        return super(SurveySurvey, self).action_send_survey()



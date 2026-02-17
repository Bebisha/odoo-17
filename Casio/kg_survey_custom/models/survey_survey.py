from odoo import api, fields, models, tools

class SurveySurvey(models.Model):
    _inherit='survey.survey'


    survey_background_image= fields.Binary('Image')
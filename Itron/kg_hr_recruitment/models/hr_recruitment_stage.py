# -*- coding: utf-8 -*-
from odoo import fields, models


class HRRecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    is_proposal = fields.Boolean('Is Contract Proposal', default=False)

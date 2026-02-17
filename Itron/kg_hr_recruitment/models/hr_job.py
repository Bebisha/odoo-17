# -*- coding: utf-8 -*-
from odoo import fields, models,api, _
from odoo.exceptions import ValidationError,AccessError



class HRJob(models.Model):
    _inherit = 'hr.job'

    job_rules = fields.Html('Roles and Responsibilities', copy=False)
    job_requirements = fields.Html('Requirements', copy=False)
    job_code = fields.Char('Job ID', copy=False,readonly= True)
    email_to = fields.Char('Email')


    @api.model
    def create(self, vals):
        if not self.env.user.has_group('base.group_system'):
            raise AccessError("Only Administrator users can create job positions.")
        vals['job_code'] = self.env['ir.sequence'].next_by_code('seq_job_position') or '/'
        result = super(HRJob, self).create(vals)
        return result

    @api.onchange('website_published')
    def _onchange_website_published(self):
        for record in self:
            if record.website_published and not record.email_to:
                raise ValidationError("Please add email before publishing.")
            if record.website_published  and not record.job_rules and not record.job_requirements :
                raise ValidationError("Please fill in Roles and Responsibilities and Job Requirements in job summary section before publishing..")
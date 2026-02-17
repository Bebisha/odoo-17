from odoo import fields, models, api, _
import json

from odoo.exceptions import ValidationError


class KgObservationRequest(models.Model):
    _name = 'observation.request'

    placer_order_number = fields.Char(string="Placer Order Number" ,copy=False, index=True, readonly=False,
                             default=lambda self: _('New'))
    universal_service_des = fields.Char(string="Universal Service Identifier" ,default =" FBC - (FULL BLOOD COUNT)")
    universal_service_code = fields.Char(string="Universal Code" , default = "1234")
    observation_date_time = fields.Datetime(string=" Observation Date Time",default=lambda self: fields.Datetime.now())
    first_name = fields.Char(string="First Name")
    middle_name = fields.Char(string="Middle Name")
    last_name = fields.Char(string="Last Name")
    priority = fields.Char(string="Priority")
    full_name = fields.Char(string="Name", compute="_compute_full_name", store=True)
    results_report_date = fields.Datetime(string="Results Report Date" ,default=lambda self: fields.Datetime.now() )
    mail_id = fields.Char(string="Email Address")
    diagnostic_service_section_id = fields.Many2one('diagnosis.service',string=" Diagnostic Service SectionID")
    result_status_id = fields.Many2one('result.status.code',string=" Result Status")
    observations_request_id = fields.Many2one('appointment.appointment',string=" Observation Request")
    order_control_id = fields.Many2one('order.control',string='Order Control')
    order_status_id = fields.Many2one('order.status', string='Order Status')
    confidentiality_id = fields.Many2one('confidentiality.code', string='Confidentiality Code')
    order_type_id = fields.Many2one('order.type', string='Order Type')
    abnormal_flag_id = fields.Many2one('abnormal.flag', string="Abnormal Flags")








    @api.depends('first_name', 'middle_name', 'last_name')
    def _compute_full_name(self):
        for record in self:
            last_name = record.last_name or ''
            middle_name = record.middle_name or ''
            first_name = record.first_name or ''

            record.full_name = f"DR.{last_name} {middle_name} {first_name}".strip()


    @api.model
    def create(self, vals):
        if vals.get('placer_order_number', _('New')) == _('New'):
            vals['placer_order_number'] = self.env['ir.sequence'].next_by_code(
                'set_id_obr') or _('New')
        return super(KgObservationRequest, self).create(vals)

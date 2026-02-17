from odoo import fields, models, api,_
from odoo.exceptions import ValidationError,UserError


class KgObservation(models.Model):
    _name = "observations.form"


    observation_identifier = fields.Many2one('documents.type', string="Observation Identifier")
    value_type=fields.Many2one('value.type',string=" Value type", default= lambda self: self.env['value.type'].search([('code', '=', 'NM')], limit=1))
    observation_value = fields.Char(string="Observation Value")
    observation_result_status = fields.Many2one('result.status.code' ,string="Observation Result Status",default= lambda self: self.env['result.status.code'].search([('code', '=', 'F')], limit=1))
    abnormal_flag_id = fields.Many2one('abnormal.flag',string="Abnormal Flags",default= lambda self: self.env['abnormal.flag'].search([('code', '=', 'N')], limit=1))
    per_org_name = fields.Char(string="Performing Organization Name")
    observations_id = fields.Many2one('appointment.appointment', string='Student')
    set_id_obx = fields.Char(string="Set ID – OBX", copy=False, index=True, readonly=False,
                             default=lambda self: _('New'))
    units= fields.Selection([
        ('bpm', 'bpm'),
        ('%','%'),
        ('mmHg','mmHg'),
        ('DegC','DegC'),
        ('cm','cm'),
        ('kg','kg'),

    ], string='Units',default="cm")
    ObservationIdentifier_units_id = fields.Many2one('units.code',string="Observation Units" ,domain="[('unit', '=', units)]",default= lambda self: self.env['units.code'].search([('code', '=', '8287-5')], limit=1) )
    references_range = fields.Char(string='References Range')
    obs_atts = fields.Binary(string="PDF Data")
    pdf_filename = fields.Char(string="File Name")
    observation_value_heart = fields.Char(string="Obsrvation HeartBeat")

    @api.constrains('obs_atts', 'pdf_filename')
    def _check_pdf_file(self):
        for record in self:
            if record.obs_atts and record.pdf_filename:
                filename = record.pdf_filename.lower()
                if not filename.endswith('.pdf'):
                    raise ValidationError("Invalid file format! Only PDF files are allowed.")

    @api.model
    def create(self, vals):
        if vals.get('set_id_obx', _('New')) == _('New'):
            vals['set_id_obx'] = self.env['ir.sequence'].next_by_code(
                'set_id_obx') or _('New')
        obs_identifier = self.env['documents.type'].browse(vals.get('observation_identifier'))
        if obs_identifier and obs_identifier.code in ['DS', 'TS'] and not vals.get('obs_atts'):
            raise UserError(_("PDF Data is required when Observation Identifier is 'Discharge Summary' or 'Transfer Summary'."))
        return super(KgObservation, self).create(vals)

    def write(self, vals):
        # Validation before record update
        for rec in self:
            obs_identifier = rec.observation_identifier
            if vals.get('observation_identifier'):
                obs_identifier = self.env['documents.type'].browse(vals['observation_identifier'])

            obs_atts_val = vals.get('obs_atts', rec.obs_atts)
            if obs_identifier and obs_identifier.code in ['DS', 'TS'] and not obs_atts_val:
                raise UserError(_("PDF Data is required when Observation Identifier is 'Discharge Summary' or 'Transfer Summary'."))

        return super(KgObservation, self).write(vals)

    # @api.constrains('observation_identifier', 'obs_atts')
    # def _check_obs_atts_required(self):
    #     """Make obs_atts required if observation_identifier code is DE or TS"""
    #     for record in self:
    #         code = record.observation_identifier.code if record.observation_identifier else False
    #         if code in ['DS', 'TS'] and not record.obs_atts:
    #             raise ValidationError(_("PDF Data is required when Observation Identifier is 'DE' or 'TS'."))
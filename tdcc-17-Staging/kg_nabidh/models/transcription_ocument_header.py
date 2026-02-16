from odoo import fields, models, api,_
from odoo.exceptions import ValidationError

class ZTranscriptionDocumentHeader(models.Model):
    _name = "transcription.document.header"


    document_completion_status = fields.Many2one('document.confidential.status', string='Document Completion Status')
    unique_document_number = fields.Char(string='Unique Document Number')
    unique_file_number = fields.Char(string='Unique Document File Name')
    activity_date_time = fields.Datetime('Activity Date / Time')
    transcription_date_time = fields.Datetime('Transcription Date Time')
    documents_type = fields.Many2one('documents.type','Document Type')
    document_completion_status_id= fields.Many2one('document.completion.status','Document Completion Status')
    document_availability_status_id= fields.Many2one('document.available.status','Document Availability Status')
    activity_provider_code = fields.Char(string="Primary Activity ProviderCode",size = 8)
    first_name = fields.Char(string="FamilyName")
    last_name = fields.Char(string="GivenName")
    originator_code_name = fields.Char(string="Originator Code Name")

    transcription_document_id= fields.Many2one('appointment.appointment', string='Transcription Document Header')
    name = fields.Char(string='Set ID – TXA', readonly=False, default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'set_id_txa') or _('New')
        res = super(ZTranscriptionDocumentHeader, self).create(vals)
        return res

    @api.constrains('activity_provider_code')
    def _check_field_length(self):
        for record in self:
            if record.activity_provider_code and len(record.activity_provider_code) != 8:
                raise ValidationError("Primary Activity Provider Code must be exactly 8 characters long.")
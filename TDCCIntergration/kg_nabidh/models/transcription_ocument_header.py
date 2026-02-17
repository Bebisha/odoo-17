from odoo import models, fields, api,_
import random
import string
import base64
import os
from odoo.exceptions import ValidationError

class ZTranscriptionDocumentHeader(models.Model):
    _name = "transcription.document.header"


    document_completion_status = fields.Many2one('document.confidential.status', string='Document Completion Status')
    unique_document_number = fields.Char(string='Unique Document Number')
    unique_file_number = fields.Char(string='Unique Document File Name' , default=lambda self: _('New'))
    activity_date_time = fields.Datetime('Activity Date / Time', default=lambda self: fields.Datetime.now())
    transcription_date_time = fields.Datetime('Report Date', default=lambda self: fields.Datetime.now())
    documents_type = fields.Many2one('documents.type','Document Type')
    document_completion_status_id= fields.Many2one('document.completion.status',string='Document Completion Status' ,
                                                   default= lambda self: self.env['document.completion.status'].search([('code', '=', 'CP')], limit=1))
    document_availability_status_id= fields.Many2one('document.available.status',string='Document Availability Status' ,
                                                     default= lambda self: self.env['document.available.status'].search([('code', '=', 'AV')], limit=1))
    activity_provider_code = fields.Char(string="Primary Activity ProviderCode",size = 8)
    first_name = fields.Char(string="FamilyName")
    last_name = fields.Char(string="GivenName")
    originator_code_name = fields.Char(string="Originator Code Name")
    attachment = fields.Binary(string="Document attachment")

    transcription_document_id= fields.Many2one('appointment.appointment', string='Transcription Document Header')
    name = fields.Char(string='Set ID – TXA', readonly=False, default=lambda self: _('New'))



    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'set_id_txa') or _('New')
            vals['unique_file_number'] = self.env['ir.sequence'].next_by_code(
                'set_txa_docs')
        res = super(ZTranscriptionDocumentHeader, self).create(vals)
        return res

    @api.constrains('activity_provider_code')
    def _check_field_length(self):
        for record in self:
            if record.activity_provider_code and len(record.activity_provider_code) != 8:
                raise ValidationError("Primary Activity Provider Code must be exactly 8 characters long.")
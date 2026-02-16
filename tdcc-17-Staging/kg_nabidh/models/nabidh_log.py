from odoo import fields, models, api,_



class KgNabidhLog(models.Model):
    _name = 'nabidh.log'

    message_type = fields.Char(
        string="Message Type",)
    kg_message_type = fields.Many2one('message.type',
        string="Message Type",)
    student = fields.Many2one('res.partner',
        string="Message Type",)
    date_message = fields.Datetime(string="Sending Time" , default=lambda self: fields.Datetime.now())
    name = fields.Char(string="Message Control ID" , readonly=False,
                                     default=lambda self: _('New'))
    message = fields.Char(string="Message")
    response = fields.Char(string="Response")
    status = fields.Char(string='Nabidh Status')
    hl7message = fields.Char(string='HL7message')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'message_control_id') or _('New')
        if 'hl7message' in vals and vals['hl7message']:
            vals['hl7message'] = self._clean_hl7(vals['hl7message'])
        res = super(KgNabidhLog, self).create(vals)
        return res

    def write(self, vals):
        if 'hl7message' in vals and vals['hl7message']:
            vals['hl7message'] = self._clean_hl7(vals['hl7message'])
        return super().write(vals)

    def _clean_hl7(self, message):
        lines = [line.strip() for line in message.strip().splitlines() if line.strip()]
        return "\n".join(lines)

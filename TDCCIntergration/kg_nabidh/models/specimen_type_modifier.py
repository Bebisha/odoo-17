from odoo import models, fields, api, _



class KgSpecimenTypeModifier(models.Model):
    _name = 'specimen.type.modifier'

    specimen_type_modifier_id = fields.Many2one('res.partner', string='Student')
    specimen_ID = fields.Char(string="Specimen ID", copy=False, index=True, readonly=False,
                                          default=lambda self: _('New'))
    specimen_type_id = fields.Many2one('specimen.type',string="Specimen Type",default= lambda self: self.env['specimen.type'].search([('code', '=', 'WB')], limit=1))
    specimen_date_time = fields.Datetime(string="Specimen Collection Time", default=lambda self: fields.Datetime.now())
    specimen_source = fields.Char(string="Specimen Source")
    specimen_condition = fields.Char(string="Specimen Condition")
    specimen_source_id = fields.Many2one('specimen.source',string="Specimen Source")
    specimen_condition_id = fields.Many2one('specimen.condition',string="Specimen Condition")
    specimen_id =  fields.Many2one('specimen.specimen',string="SpecimenID")

    @api.model
    def create(self, vals):
        if vals.get('specimen_ID', _('New')) == _('New'):
            vals['specimen_ID'] = self.env['ir.sequence'].next_by_code(
                'specimen_id_sequence') or _('New')
        return super(KgSpecimenTypeModifier, self).create(vals)
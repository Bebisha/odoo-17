from odoo import fields, models, api,_


class KgPatientAllergyInformation(models.Model):
    _name = "patient.allergy.information"


    patient_allergy_id = fields.Many2one('appointment.appointment',string='Student')

    allergy_type_codes = fields.Many2one('allergen.type.code',string="Allergen Code",default= lambda self: self.env['allergen.type.code'].search([('code', '=', '417532002')], limit=1))

    allergy_code_des= fields.Many2one('allergen.code',string="Allergy Type Code",default= lambda self: self.env['allergen.code'].search([('code', '=', 'FA')], limit=1))

    # allergy_type = fields.Many2one('allergen.type.code',string="Code Description",default= lambda self: self.env['allergen.type.code'].search([('code', '=', '417532002')], limit=1) )
    allergy_severty_code = fields.Many2one('allergy.severty.code',string="Allergy Severity Code",default= lambda self: self.env['allergy.severty.code'].search([('code', '=', 'MI')], limit=1))
    allergy_reaction_code = fields.Many2one('allergy.reaction.code',string="Allergy Reaction Code",default= lambda self: self.env['allergy.reaction.code'].search([('code', '=', 'Nasal congestion')], limit=1))
    set_id_al1 = fields.Char(string='Set ID – AL1 ', copy=False, index=True, readonly=False,
                             default=lambda self: _('New'))
    al1_date = fields.Datetime('Identification Date ', default=lambda self: fields.Datetime.now())

    @api.model
    def create(self, vals):
        if vals.get('set_id_al1', _('New')) == _('New'):
            vals['set_id_al1'] = self.env['ir.sequence'].next_by_code(
                'set_id_al1') or _('New')
        return super(KgPatientAllergyInformation, self).create(vals)





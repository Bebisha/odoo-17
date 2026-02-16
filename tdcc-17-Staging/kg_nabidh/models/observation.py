from odoo import fields, models, api,_


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
    obs_atts = fields.Binary(string="Value")
    observation_value_heart = fields.Char(string="Obsrvation HeartBeat")


    @api.model
    def create(self, vals):
        if vals.get('set_id_obx', _('New')) == _('New'):
            vals['set_id_obx'] = self.env['ir.sequence'].next_by_code(
                'set_id_obx') or _('New')
        return super(KgObservation, self).create(vals)
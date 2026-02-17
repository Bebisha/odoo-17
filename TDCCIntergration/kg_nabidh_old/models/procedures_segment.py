from odoo import fields, models, api,_


class KgProceduresSegment(models.Model):
    _name = "procedures.segment"


    procedure_code = fields.Char(related='procedure_id.code',string="Procedure Code")
    procedure_description = fields.Char(string="Procedure Description")
    procedure_id =  fields.Many2one('procedure.procedure',string="Procedure Description")
    physician_id = fields.Many2one('res.partner', string="Physician",
                                   domain=[('is_physician', '=', True)],
                                   copy=False, )

    surgeon = fields.Char(string="Surgeon" ,)
    procedure_priority = fields.Selection([('1' ,'indicates Primary Procedure'),('2', 'indicated Secondary Procedures')] ,string="Procedure Priority")


    procedures_segment_id = fields.Many2one('appointment.appointment', string='Student')
    set_id_prl = fields.Char(string='Set ID – PR1 ', copy=False, index=True, readonly=False,
                             default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        if vals.get('set_id_prl', _('New')) == _('New'):
            vals['set_id_prl'] = self.env['ir.sequence'].next_by_code(
                'set_id_prl') or _('New')
        return super(KgProceduresSegment, self).create(vals)

    @api.onchange('physician_id')
    def onchnage_physician_id(self):
        for rec in self:
            if rec.physician_id:
                rec.surgeon = 'Dr. ' + rec.physician_id.name
            else:
                rec.surgeon = False

class KgProcedureProcedure(models.Model):
    _name = 'procedure.procedure'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")

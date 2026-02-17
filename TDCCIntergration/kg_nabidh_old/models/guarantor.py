from odoo import fields, models, api,_


class KgGuarantor(models.Model):
    _name = "guarantor.form"

    guarantor_name = fields.Char(string="Guarantor Name")

    guarantor_id = fields.Many2one('res.partner', string='Student')
    set_id_gtl = fields.Char(string='Set ID – GTL ', copy=False, index=True, readonly=False,
                             default=lambda self: _('New'))
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    full_name = fields.Char(string="guarantor Name", compute="_compute_full_name", store=True)
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    states = fields.Many2one('state.form', string='State')
    country = fields.Many2one('country.form', string='Country')
    zip = fields.Integer("ZIP")
    addres_type = fields.Many2one('address.type', string="Address type")
    complete_address = fields.Char(string='Address', compute='_compute_complete_address')
    phone_number = fields.Char(string='Phone Number')
    guarantor_relationship = fields.Many2one('relationship.form',string="Guarantor Relationship")

    @api.model
    def create(self, vals):
        if vals.get('set_id_gtl', _('New')) == _('New'):
            vals['set_id_gtl'] = self.env['ir.sequence'].next_by_code(
                'set_id_gtl') or _('New')
        return super(KgGuarantor, self).create(vals)

    @api.depends('first_name', 'last_name')
    def _compute_full_name(self):
        for record in self:
            last_name = record.last_name or ''
            first_name = record.first_name or ''

            record.full_name = f"{last_name} {first_name}"

    @api.depends('street', 'city', 'states', 'country', 'addres_type')
    def _compute_complete_address(self):
        for record in self:
            street = record.street or ''
            city = record.city or ''
            state = record.states.name or ''
            zip = record.zip or ''
            country = record.country.code or ''
            addres_type = record.addres_type.name or ''

            record.complete_address = f"{street},{city},{state},{zip},{country},{addres_type}"


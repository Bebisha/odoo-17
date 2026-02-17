from odoo import fields, models, api,_


class KgAssociatedParties(models.Model):
    _name= "associated.parties"


    first_name = fields.Char(string="First Name")
    middle_name = fields.Char(string="Middle Name")
    last_name = fields.Char(string="Last Name")
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    states = fields.Many2one('state.form', string='State')
    country = fields.Many2one('country.form', string='Country')
    zip = fields.Integer("ZIP")
    addres_type = fields.Many2one('address.type',string="Address type")
    complete_address = fields.Char(string='Address', compute='_compute_complete_address')
    phone_number =fields.Char(string='Phone Number')

    full_name = fields.Char(string="Name", compute="_compute_full_name", store=True)

    emergency_contact = fields.Many2one('contact.role',string="Contact Role")
    relationship = fields.Many2one('relationship.form',string="Relationship")

    associated_parties_id = fields.Many2one('res.partner', string='Student')
    set_id_nk1 = fields.Char( string='Set ID – NK1' ,copy=False, index=True, readonly=False,
                                    default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        if vals.get('set_id_nk1', _('New')) == _('New'):
            vals['set_id_nk1'] = self.env['ir.sequence'].next_by_code(
                'set_id_nk1') or _('New')
        return super(KgAssociatedParties, self).create(vals)

    @api.depends('first_name', 'middle_name', 'last_name')
    def _compute_full_name(self):
        for record in self:
            last_name = record.last_name or ''
            middle_name = record.middle_name or ''
            first_name = record.first_name or ''

            record.full_name = f"{last_name} {middle_name} {first_name}"



    @api.depends('street', 'city', 'states', 'country','addres_type')
    def _compute_complete_address(self):
        for record in self:
            street = record.street or ''
            city = record.city or ''
            state = record.states.name or ''
            zip = record.zip or ''
            country = record.country.code or ''
            addres_type = record.addres_type.name or ''
            record.complete_address = f"{street},{city},{state},{zip},{country},{addres_type}"

    @api.onchange('country')
    def onchange_country_id(self):
        if self.country:
            country_code = self.env['country.form'].browse(self.country.id).code
            if country_code:
                self.phone_number = '+' + country_code + ' '
            else:
                self.phone_number = " "

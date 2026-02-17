from odoo import fields, models, api,_
from odoo.exceptions import ValidationError

class KgCommonOrder(models.Model):
    _name= "common.order"

    order_control = fields.Many2one('order.control' , string="Order Control" ,default= lambda self: self.env['order.control'].search([('code', '=', 'OK')], limit=1))
    order_status = fields.Many2one('order.status',string="Order Status" ,default= lambda self: self.env['order.status'].search([('code', '=', 'CM')], limit=1))
    date_transaction = fields.Datetime(string="Date / Time of Transaction", default=lambda self: fields.Datetime.now())
    start_date = fields.Datetime(string="Date / Time of Start", default=lambda self: fields.Datetime.now())
    end_date = fields.Datetime(string="Date / Time of End", default=lambda self: fields.Datetime.now())
    confidentiality_code = fields.Many2one('confidentiality.code',string="Confidentiality Code" ,default= lambda self: self.env['confidentiality.code'].search([('code', '=', 'U')], limit=1))
    order_type = fields.Many2one('order.type',string="Order Type",default= lambda self: self.env['order.type'].search([('code', '=', 'MED')], limit=1))
    name = fields.Char(string="Order Number" , readonly=False,
                                     default=lambda self: _('New') )
    ordering_provider = fields.Char(string="Ordering Provider",default="12345678",size = 8)
    quantity = fields.Char(string="Quantity")
    interval = fields.Char(string="Interval")
    duration = fields.Char(string="Duration")
    priority = fields.Char(string="Priority")
    text = fields.Char(string="Text")
    family_name = fields.Char(string="Family Name")
    given_name = fields.Char(string="Given Name")
    common_order_id = fields.Many2one('appointment.appointment', string='Common Order')

    full_name = fields.Char(string="Attending Doctor", compute="_compute_full_name", store=True)

    @api.depends('family_name', 'given_name')
    def _compute_full_name(self):
        for record in self:
            family_name = record.family_name or ''
            given_name = record.given_name or ''

            record.full_name = f"DR. {given_name} {family_name}".strip()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'placer_order_number') or _('New')
        res = super(KgCommonOrder, self).create(vals)
        return res

    @api.constrains('ordering_provider')
    def _check_field_length(self):
        for record in self:
            if record.ordering_provider and len(record.ordering_provider) != 8:
                raise ValidationError("Common OrderYour Field must be exactly 8 characters long.")

class KgPharmacyOrder(models.Model):
    _name= "pharmacy.order"

    requested_give_code = fields.Char(string="Medication Code",default="0000-000000-0000")
    requested_give_name = fields.Char(string="Medicine Name",default="DESLORATADINE 5 MG TABLET")
    requested_amount_minimum = fields.Char(string="Requested Give Amount – Minimum",default = "20 in 20mg")
    requested_given_unit= fields.Char(string="Unit of Measure")
    dosage= fields.Char(string="Dosage")
    pharmacy_order_id = fields.Many2one('appointment.appointment', string='Pharmacy')
    frequency = fields.Char(string="Frequency")
    administratio_time = fields.Datetime(string="Administration Time", default=lambda self: fields.Datetime.now())
    expiration_date = fields.Datetime(string="Expiration Date", default=lambda self: fields.Datetime.now())
    status = fields.Selection([('Active', 'A'), ('Inactivate', 'I')],
                                         help="A for ‘Active’ or I for ‘Inactive",
                                         string="Status")

    providers_administration_instructions = fields.Many2one('route.form', string='Route Of Administration',default= lambda self: self.env['route.form'].search([('code', '=', 'LOCAL')], limit=1))


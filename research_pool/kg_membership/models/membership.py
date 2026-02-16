
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

from odoo.fields import Many2many


class KGMembershipLine(models.Model):
    _inherit = 'membership.membership_line'


class KGProductTemplate(models.Model):
    _inherit = "product.template"

    interval_type = fields.Selection([
        ('days', 'Days'),
        ('months', 'Months'),
        ('years', 'Years')
    ], string='Interval Type', required=True)

    interval_value = fields.Integer(string='Interval Value', default=1)

    @api.onchange('membership_date_from', 'interval_type', 'interval_value')
    def _onchange_date_from(self):
        if self.membership_date_from and self.interval_value:
            if self.interval_type == 'days':
                self.membership_date_to = self.membership_date_from + relativedelta(days=self.interval_value)
            elif self.interval_type == 'months':
                self.membership_date_to = self.membership_date_from + relativedelta(months=self.interval_value)
            elif self.interval_type == 'years':
                self.membership_date_to = self.membership_date_from + relativedelta(years=self.interval_value)
        else:
            self.membership_date_to = False


class KGPartner(models.Model):
    _inherit = 'res.partner'

    is_membership = fields.Boolean(string="IS Membership")
    is_associate_member = fields.Boolean(string='Associate Member',
                                         help="A member with whom you want to associate your membership."
                                              "It will consider the membership state of the associated member.")
    membership_number = fields.Char(string="Membership Number", copy=False, index=True, readonly=False,
                                    default=lambda self: _('New'))
    associate_membership_number = fields.Char(string="Associate Member Number", copy=False, index=True, readonly=False,
                                              default=lambda self: _('New'))

    membership_counter = fields.Integer(string="Membership Counter", default=1,
                                        help="Counter for membership letters (A, B, C, ..., Z, AA, AB, etc.)")

    associate_member_ids = Many2many('res.partner', string="Associate Member", column1='assoc_me_id',
                                     column2='associate_membership_row', relation="associate_member_id",compute='_onchange_associate_memb')

    associate_member_count = fields.Integer(
        string="Associate Member",
        compute="_compute_associate_member_count"
    )

    @api.depends('membership_number')
    def _onchange_associate_memb(self):
        self.associate_member_ids =False
        if self.membership_number !='New':
            l=self.env['res.partner'].search([('membership_number', '=', self.membership_number),('id', '!=', self._origin.id)])
            print(l)
            self.associate_member_ids = [(6,0,l.ids)]


    def _compute_associate_member_count(self):
        for order in self:
            order.associate_member_count = self.env['res.partner'].search_count(
                [('membership_number', '=', self.membership_number), ('id', '!=', self.id)])

    @api.model
    def create(self, vals):
        if vals.get('is_membership', False):
            vals['membership_number'] = self.env['ir.sequence'].next_by_code('membership_sequence') or '/'
        partner = super(KGPartner, self).create(vals)

        return partner

    @api.model
    def write(self, vals):
        if vals.get('is_membership', False):
            vals['membership_number'] = self.env['ir.sequence'].next_by_code('membership_sequence') or '/'
        partner = super(KGPartner, self).write(vals)

        return partner

    def action_associate_member(self):
        for record in self:
            if record.is_membership:
                current_counter = record.membership_counter
                letter = chr(64 + current_counter)

                if record.membership_number:
                    record.associate_membership_number = f"{record.membership_number}-{letter}"
                record.membership_counter += 1

                # Prepare the context to pass the membership_number to the new form view
                context = {
                    'default_is_associate_member': True,
                    'default_associate_membership_number': record.associate_membership_number,
                    'default_membership_number': record.membership_number,
                }

                return {
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'name': _('Associate Member'),
                    'view_mode': 'form',
                    'res_model': 'res.partner',
                    'context': context,
                }

    def action_associate_member_views(self):
        # existing_partners = self.env['res.partner'].search([
        #     # Example search criteria: find partners that can be associated
        #     ('membership_number', '=', self.membership_number), ('id', '!=', self.id)
        # ])
        # print(existing_partners,'existing_partners')
        #
        # # Link the found partners to the membership record in the Many2many field
        # if existing_partners:
        #     self.associate_member_ids |= existing_partners
        # # Return the action to open the associated member form
        return {
            'type': 'ir.actions.act_window',
            'name': _('Associate Member'),
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'domain': [('membership_number', '=', self.membership_number), ('id', '!=', self.id)],
            'context': {'create': False}

        }

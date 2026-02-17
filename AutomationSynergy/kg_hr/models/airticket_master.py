from odoo import models, fields, api
from odoo.exceptions import UserError


class AirTicketMaster(models.Model):
    _name = 'airticket.master'

    name = fields.Char(compute='compute_name', store=True)
    ticket_count = fields.Integer('Ticket Count', required=True)
    year = fields.Integer('Year')

    @api.depends('ticket_count', 'year')
    def compute_name(self):
        for rec in self:
            if rec.ticket_count == 0 or rec.year == 0:
                rec.name = False
            else:
                rec.name = f"{rec.ticket_count} Ticket / {rec.year} Year"

    @api.model
    def create(self, values):
        if 'ticket_count' in values and values['ticket_count'] == 0:
            raise UserError('Specify the ticket count')
        if 'year' in values and values['year'] == 0:
            raise UserError('Specify the year')

        return super(AirTicketMaster, self).create(values)

    def write(self, values):
        if 'ticket_count' in values and values['ticket_count'] == 0:
            raise UserError('Specify the ticket count')
        if 'year' in values and values['year'] == 0:
            raise UserError('Specify the year')

        return super(AirTicketMaster, self).write(values)

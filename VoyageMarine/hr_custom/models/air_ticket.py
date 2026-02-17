from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError


class EmployeeTicketAttachment(models.Model):
    _inherit = 'ir.attachment'
    doc_attach_rel1 = fields.Many2many('air.ticket', 'doc_attachment_id1', 'attach_id3', 'doc_id2',
                                       string="Attachment", invisible=1)


class AirTicket(models.Model):
    _name = 'air.ticket'

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee')
    departure_date = fields.Date('Issue Date', default=fields.date.today())
    from_loc = fields.Many2one('res.country.state', string="From Location")
    to_location = fields.Many2one('res.country.state', string="To Location")
    doc_attachment_id1 = fields.Many2many('ir.attachment', 'doc_attach_rel1', 'doc_id2', 'attach_id3',
                                          string=" Attachment", help='You can attach documents', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel')], default='draft', string="State")
    amount = fields.Float('Amount', readonly=True, force_save=True)
    is_used = fields.Boolean(default=False, copy=False)
    region_id = fields.Many2one('air.ticket.rate', string="Region")
    leave_id = fields.Many2one('hr.leave', string="Leave")

    @api.onchange('region_id')
    def onchange_region(self):
        if self.region_id:
            self.amount = self.region_id.amount

    def action_confirm(self):
        tkt = self.env['air.ticket'].search(
            [('employee_id', '=', self.employee_id.id), ('state', '=', 'confirm')])
        emp_yr = 0
        if self.employee_id.airticket_id:
            emp_yr = self.employee_id.airticket_id.year
        current_period = self.departure_date
        period_date = current_period - relativedelta(years=emp_yr)  # Approximating years as 365 days
        filtered_tkt = tkt.filtered(lambda x: period_date < x.departure_date <= current_period)
        if self.employee_id.airticket_id and (len(filtered_tkt) >= self.employee_id.airticket_id.ticket_count):
            raise ValidationError('The ticket count assigned to the employee has been exceeded.')
        self.state = 'confirm'

    def action_cancel(self):
        self.state = 'cancel'

    @api.constrains('doc_attachment_id1')
    def check_doc_attachment_id_missing(self):
        for rec in self:
            if len(rec.doc_attachment_id1) == 0:
                raise ValidationError(('Attachment Missing..'))


class AirTicketRate(models.Model):
    _name = 'air.ticket.rate'
    _rec_name = 'region'

    region = fields.Char()
    code = fields.Char()
    amount = fields.Float(required=True)

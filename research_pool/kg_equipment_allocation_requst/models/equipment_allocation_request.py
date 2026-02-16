# -*- encoding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models,_
from odoo.fields import Date


class EquipmentAllocationRequest(models.Model):

    _name = "equipment.allocation.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]




    name = fields.Char(compute="_compute_name")

    employee_id = fields.Many2one(
        comodel_name="hr.employee",string="Employee"
    )

    equipment_id = fields.Many2one(
        comodel_name="maintenance.equipment",
        required=True,string="Equipment",
        domain="[('state', '=', available)]",
    )

    request_number = fields.Char(string="Request Number", copy=False, index=True, readonly=False,
                                default=lambda self: _('New'))
    allocation_type = fields.Selection(
        [('on_demand', 'On Demand'), ('permanently', 'Permanently')],
        string="Allocation Type",
        default='on_demand',

    )
    duration_type = fields.Selection(
        [('months', 'Months'), ('years', 'Years'), ('days', 'Days')],
        string="Duration Type", default='months'
    )
    duration_value = fields.Integer(string="Duration Value", default=1)

    duration = fields.Integer(string="Duration")

    start_date = fields.Date( string="Request Date" ,default=lambda self: fields.Datetime.now())
    allocation_date =fields.Datetime(string="Allocation Date")
    return_date =fields.Datetime(string="Return Date")
    state = fields.Selection(
        [
            ("new", "New"),
            ("waiting", "Waiting for Approval"),
            ("allocated", "Allocated"),
            ("rejected", "Rejected"),
            ("return", "Return"),
        ],
        default="new",
        tracking=True,
    )
    description = fields.Text(string='Description', translate=True)

    expected_return_date = fields.Datetime(string="Expected Return Date", compute='_compute_expected_return_date',
                                           store=True)

    @api.depends("allocation_date", "duration","duration_type")
    def _compute_expected_return_date(self):
        for record in self:
            if record.allocation_date and record.duration_type and record.duration_value:
                allocation_date = fields.Datetime.from_string(record.allocation_date)
                if record.duration_type == 'months':
                    expected_return_date = allocation_date + timedelta(days=record.duration_value * 30)
                elif record.duration_type == 'years':
                    expected_return_date = allocation_date + timedelta(days=record.duration_value * 365)
                else:  # Assuming 'days'
                    expected_return_date = allocation_date + timedelta(days=record.duration_value)
                record.expected_return_date = expected_return_date
    @api.model
    def create(self, vals):
        if vals.get('request_number', _('New')) == _('New'):
            vals['request_number'] = self.env['ir.sequence'].next_by_code(
                'allocation_number') or _('New')
        res = super(EquipmentAllocationRequest, self).create(vals)
        return res


    @api.depends("equipment_id", "employee_id")
    def _compute_name(self):
        for rec in self:
            if rec.equipment_id.name and rec.employee_id.name:
                rec.name = "{} to {}".format(rec.equipment_id.name, rec.employee_id.name)
            else:
                rec.name = False


    def _validate_allocation_vals(self):
        return {
            "state": "valid",
            "start_date": fields.Date.context_today(self)
            if not self.start_date
            else self.start_date,
        }


    @api.onchange('duration_type', 'duration_value')
    def _onchange_duration(self):
        for rec in self:
            if rec.duration_type and rec.duration_value:
                if rec.duration_type == 'months':
                    rec.duration = rec.duration_value * 30  # Assuming 30 days in a month
                elif rec.duration_type == 'years':
                    rec.duration = rec.duration_value * 365  # Assuming 365 days in a year
                else:
                    rec.duration = rec.duration_value

    @api.onchange('duration')
    def _onchange_duration_to_parts(self):
        for rec in self:
            if rec.duration:
                if rec.duration_type == 'months':
                    rec.duration_value = rec.duration // 30
                elif rec.duration_type == 'years':
                    rec.duration_value = rec.duration // 365
                else:
                    rec.duration_value = rec.duration

    # @api.depends('stop', 'start')
    # def _compute_duration(self):
    #     for event in self:
    #         event.duration = self._get_duration(event.start, event.stop)
    # def _get_duration(self, start, stop):
    #     """ Get the duration value between the 2 given dates. """
    #     if not start or not stop:
    #         return 0
    #     duration = (stop - start).total_seconds() / 3600
    #     return round(duration, 2)

    def submit_to_manager(self):
        return self.write({"state": "waiting"})
        print("ffffffffffffffff")
    def validate_allocation(self):
        print("hhhhhhhh")
        allocation_date = fields.Datetime.now()
        self.equipment_id.write({'employee_id': self.employee_id.id})
        self.equipment_id.state = 'allocated'
        # self.equipment_id.owner_user_id = True
        return self.write({"state": "allocated","allocation_date":allocation_date})


    def reject_allocation(self):
        print("hpppppppp")
        return self.write({"state": "rejected"})
    def return_allocation(self):
        return_date = fields.Datetime.now()
        print("uuuuuuuu")
        return self.write({"state": "return","return_date":return_date})

    # @api.onchange('employee_id')
    # def _onchange_employee_id(self):
    #     if self.employee_id:
    #         # Assuming you have a field named 'equipment_id' on the 'hr.employee' model
    #         employee_equipment = self.employee_id.equipment_id
    #         if employee_equipment:
    #             self.equipment_id = employee_equipment.id

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    allocation_request_id = fields.Many2one(
        'equipment.allocation.request', string="Allocation Request")

    state = fields.Selection(
        [
            ("available", "Available"),
            ("allocated", "Allocated"),
        ],
        default="available",
        tracking=True,
    )


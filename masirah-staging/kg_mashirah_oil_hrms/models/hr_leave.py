from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HRLeaveInherit(models.Model):
    _inherit = "hr.leave"

    relation = fields.Selection([
        ('mother', 'Mother'),
        ('father', 'Father'),
        ('spouse', 'Spouse'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('grandparents', 'Grandparents'),
        ('daughter', 'Daughter'),
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
        ('cousin', 'Cousin'),
        ('brother-in-law', 'Brother-in-law'),
        ('sister-in-law', 'Sister-in-law'),
        ('father-in-law', 'Father-in-law'),
        ('mother-in-law', 'Mother-in-law'),
    ], string="Relation")
    is_compassionate_leave = fields.Boolean(default=False)
    balance_leave = fields.Float(string="Leave Balance")
    leave_accrued = fields.Float(string="Leave Accrued")
    leaves_taken = fields.Float(string="Leaves Taken")
    approval_date = fields.Date('Approval Date')

    # @api.onchange('holiday_status_id', 'employee_id', 'date_from', 'date_to')
    @api.depends('employee_id', 'holiday_status_id', 'number_of_days_display')
    @api.onchange('employee_id', 'holiday_status_id', 'number_of_days_display')
    def set_balance_accrued_leaves(self):
        for rec in self:
            if rec.holiday_status_id:
                hr_leave_allocation_id = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', rec.employee_id.id),
                     ('holiday_status_id', '=', rec.holiday_status_id.id), ('state', '=', 'validate')])
                rec.leave_accrued = sum(hr_leave_allocation_id.mapped('number_of_days'))
                hr_leave_id = self.env['hr.leave'].search(
                    [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.holiday_status_id.id),
                     ('state', '=', 'validate')])
                rec.balance_leave = rec.leave_accrued - sum(hr_leave_id.mapped('number_of_days'))
        # if self.holiday_status_id and self.employee_id:
        #     mapped_days = self.mapped('holiday_status_id').get_employees_days(self.mapped('employee_id').ids)
        #     for holiday in self:
        #         if holiday.holiday_type != 'employee' or not holiday.employee_id or holiday.holiday_status_id.requires_allocation == 'no':
        #             self.balance_leave = 0.0
        #             self.leave_accrued = 0.0
        #             self.leaves_taken = 0.0
        #             continue
        #         leave_days = mapped_days[holiday.employee_id.id][holiday.holiday_status_id.id]
        #         self.balance_leave = leave_days.get('remaining_leaves') or 0.0
        #         self.leave_accrued = leave_days.get('max_leaves') or 0.0
        #         self.leaves_taken = leave_days.get('leaves_taken') or 0.0

    def action_validate(self):
        res = super(HRLeaveInherit, self).action_validate()
        self.approval_date = fields.Date.today()
        self.balance_leave = self.balance_leave - self.number_of_days_display
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HRLeaveInherit, self).create(vals_list)
        for vals in vals_list:
            maternity_leave_id = self.env.ref('kg_mashirah_oil_hrms.maternity_leave_type').id
            haj_leave_id = self.env.ref('kg_mashirah_oil_hrms.haj_leave_type').id
            marriage_leave_id = self.env.ref('kg_mashirah_oil_hrms.marriage_leave_type').id

            if vals['holiday_status_id'] and vals['employee_id']:

                if vals['holiday_status_id'] == maternity_leave_id:
                    maternity_hr_leave_id = self.env['hr.leave'].search(
                        [('holiday_status_id', '=', maternity_leave_id), ('employee_id', '=', vals['employee_id']),
                         ('state', '=', 'validate')])
                    if len(maternity_hr_leave_id) == 3:
                        raise ValidationError(
                            "Maternity Leave can be taken only 3 times in a tenure. You have already taken it.")

                if vals['holiday_status_id'] == haj_leave_id:
                    haj_hr_leave_id = self.env['hr.leave'].search(
                        [('holiday_status_id', '=', haj_leave_id), ('employee_id', '=', vals['employee_id']),
                         ('state', '=', 'validate')])
                    if len(haj_hr_leave_id) == 1:
                        raise ValidationError(
                            "Haj Leave can be taken only once in a tenure. You have already taken it.")

                if vals['holiday_status_id'] == marriage_leave_id:
                    marriage_hr_leave_id = self.env['hr.leave'].search(
                        [('holiday_status_id', '=', marriage_leave_id), ('employee_id', '=', vals['employee_id']),
                         ('state', '=', 'validate')])
                    if len(marriage_hr_leave_id) == 1:
                        raise ValidationError(
                            "Marriage Leave can be taken only once in a tenure. You have already taken it.")

        return res

    @api.onchange('holiday_status_id', 'relation')
    def check_compassionate_leave(self):
        for rec in self:
            compassionate_leave_id = self.env.ref('kg_mashirah_oil_hrms.compassionate_leave_type').id
            if rec.holiday_status_id and rec.holiday_status_id.id == compassionate_leave_id:
                rec.is_compassionate_leave = True
            else:
                rec.is_compassionate_leave = False

    @api.constrains('is_compassionate_leave')
    def check_take_leaves(self):
        for rec in self:
            if rec.is_compassionate_leave and rec.relation:
                if (rec.relation == 'mother' or rec.relation == 'father' or rec.relation == 'spouse'
                        or rec.relation == 'son' or rec.relation == 'daughter'):
                    if rec.number_of_days > 10:
                        raise ValidationError("Compassionate Leave can be taken maximum 10days only")
                else:
                    if rec.number_of_days > 3:
                        raise ValidationError("Compassionate Leave can be taken maximum 3days only")

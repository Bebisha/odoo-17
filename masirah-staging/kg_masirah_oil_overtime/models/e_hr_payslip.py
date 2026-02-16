# -*- coding: utf-8 -*-
######################################################################################
#
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
from odoo import models, api, fields, Command


class PayslipOverTime(models.Model):
    _inherit = 'hr.payslip'

    overtime_ids = fields.Many2many('hr.overtime')
    days_no_tmp = fields.Float('Hours', readonly=True)
    ot_amount = fields.Float(string="Overtime Amount")

    @api.onchange('employee_id')
    def get_employee_ids(self):
        for rec in self:
            if rec.employee_id:
                ot_id = self.env['hr.overtime'].search(
                    [('employee_id', '=', rec.employee_id.id), ('type', '=', 'cash'),
                     ('state', '=', 'approved'), ('contract_id', '=', rec.contract_id.id),
                     ('payslip_paid', '=', False), ('date_from', '>=', rec.date_from)])
                if ot_id:
                    for vals in ot_id:
                        rec.overtime_ids = [(4, vals.id)]
                    rec.ot_amount = sum(ot_id.mapped('overtime_amount'))
                    rec.days_no_tmp = sum(ot_id.mapped('days_no_tmp'))
                else:
                    rec.overtime_ids = False
                    rec.ot_amount = 0.00
                    rec.days_no_tmp = 0.00



    def action_payslip_done(self):
        """
        function used for marking paid overtime
        request.

        """
        for recd in self.overtime_ids:
            if recd.type == 'cash':
                recd.payslip_paid = True
        return super(PayslipOverTime, self).action_payslip_done()

    basic_salary = fields.Float(string='Basic Salary')

    @api.depends('basic_salary', 'days_no_tmp')
    def _compute_overtime(self):
        for record in self:
            if record.days_no_tmp > 8:
                overtime_pay = ((record.basic_salary / 31) / record.days_no_tmp) * 1.25
            else:
                overtime_pay = 0

            record.amount = overtime_pay

from datetime import timedelta, datetime

from odoo import models, fields


class AttendanceReport(models.TransientModel):
    _name = 'late.report'
    _description = "Late Report"
    _rec_name = 'type_arrival'

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, required=True)
    type_arrival = fields.Selection([
        ('early_departure', 'Early Departure'),
        ('late_arrival', 'Late Arrival')
    ], string="Type", )

    def action_view_requests(self):
        domain = [
            ('company_name', '=', self.company_id.id),
            ('type', '=', self.type_arrival),
        ]

        # records = self.env['early.late.request'].sudo().search(domain)
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Early/Late Requests',
        #     'view_mode': 'tree,form',
        #     'res_model': 'early.late.request',
        #     'domain': domain,
        #     'context': dict(self.env.context,
        #                     group_by='employee_id',),
        # }

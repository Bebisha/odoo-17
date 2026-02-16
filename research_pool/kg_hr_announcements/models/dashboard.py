from datetime import timedelta

from odoo import models, api, fields
from datetime import datetime



class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_upcoming(self):
        # Announcements
        announcements = self.env['hr.announcement'].search([
            ('state', '=', 'approved'),
            ('date_start', '<=', fields.Date.context_today(self)),
            ('date_end', '>=', fields.Date.context_today(self)),
        ])
        announcement_data = []
        for announcement in announcements:
            announcement_data.append({
                'id': announcement.id,
                'name': announcement.name,
            })

        return {

            'announcements': announcement_data,
        }


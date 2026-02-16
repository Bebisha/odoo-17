# -- coding: utf-8 --

import base64
from datetime import timedelta

from odoo import models, api, fields
from datetime import datetime



class KGEmployee(models.Model):
    _inherit = 'hr.employee'



    @api.model
    def get_upcoming(self):
        today = fields.Datetime.now()
        future_date = today + timedelta(days=15)
        # Birthday
        employees = self.env['hr.employee'].search([])
        birthdays = []
        for employee in employees:
            if employee.birthday:
                dob = fields.Date.from_string(employee.birthday)
                today = fields.Datetime.now().date()  # Ensure to get the date only
                next_birthday = datetime(today.year, dob.month, dob.day).date()
                if next_birthday < today:
                    next_birthday = datetime(today.year + 1, dob.month, dob.day).date()

                days_until_birthday = (next_birthday - today).days
                if 0 <= days_until_birthday <= 15:
                    image_url = f"/web/image?model=hr.employee&id={employee.id}&field=image_1920"
                    birthdays.append({
                        'id': employee.id,
                        'name': employee.name,
                        'birthday': dob.strftime('%B %d'),
                        'job_id': employee.job_id.name,
                        'image_url': image_url
                    })
        # Events
        events = self.env['event.event'].search([
            ('date_begin', '<=', future_date),
            ('date_begin', '>=', today),
            '&', ('date_end', '<=', future_date),
            ('date_end', '>=', today)
        ])
        event_data = []
        if events:
            for event in events:
                if event and event.address_id:
                    event_data.append({
                        'id':event.id,
                        'name': event.name,
                        'date_begin': event.date_begin,
                        'date_end': event.date_end,
                        'address_id': event.address_id.name,
                        'event_type_id': event.event_type_id.name,
                        # 'is_online': event.is_online
                    })
                else:
                    print("Event or address_id is undefined:", event)
        else:
            print("No events found.")

        return {
            'birthday': birthdays,
            'event': event_data,
        }



class KGCrmLead(models.Model):
    """crm inherited model"""
    _inherit = 'crm.lead'

    @api.model
    def get_tiles_data(self):
        """ Return the tile data"""
        company_id = self.env.company
        leads = self.search([('company_id', '=', company_id.id),
                             ('user_id', '=', self.env.user.id)])
        my_leads = leads.filtered(lambda r: r.type == 'birthday')
        my_opportunity = leads.filtered(lambda r: r.type == 'opportunity')
        currency = company_id.currency_id.symbol
        expected_revenue = sum(my_opportunity.mapped('expected_revenue'))
        return {
            'total_leads': len(my_leads),
            'total_opportunity': len(my_opportunity),
            'expected_revenue': expected_revenue,
            'currency': currency,
        }

from datetime import timedelta

from odoo import models, api, fields
from datetime import datetime



class Employee(models.Model):
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
                    birthdays.append({
                        'id': employee.id,
                        'name': employee.name,
                        'birthday': dob.strftime('%B %d'),
                        'job_id': employee.job_id.name
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
                        'name': event.name,
                        'date_begin': event.date_begin,
                        'date_end': event.date_end,
                        'address_id': event.address_id.country_id.name,
                        # 'is_online': event.is_online
                    })
                else:
                    print("Event or address_id is undefined:", event)
        else:
            print("No events found.")

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
            'birthday': birthdays,
            'event': event_data,
            'announcements': announcement_data,
        }


# from odoo import models, api
#
#
# class Employee(models.Model):
#     _inherit = 'hr.employee'
#
#     @api.model
#     def get_upcoming(self):
# #         Birthday
#         self._cr.execute("""
#             SELECT *,
#                     (to_char(dob, 'ddd')::int-to_char(
#                     now(), 'ddd')::int+total_days)%total_days AS dif
#             FROM
#                 (SELECT he.id,he.name,
#                         to_char(he.birthday, 'Month dd') AS birthday,
#                         hj.name AS job_id,
#                         he.birthday AS dob,
#                        (to_char((to_char(now(), 'yyyy')||'-12-31')::date,
#                        'ddd')::int) AS total_days
#                               FROM hr_employee he
#                               JOIN hr_job hj ON hj.id = he.job_id ) birth
#                         WHERE (to_char(dob, 'ddd')::int-to_char(now(), 'DDD')
#                                      ::int+total_days)%
#                                      total_days BETWEEN 0 AND 15
#                         ORDER BY dif
#             """)
#         birthday = self._cr.dictfetchall()
#
#
#     @api.model
#     def get_tiles_data(self):
#             """ Return the tile data"""
#             company_id = self.env.company
#             leads = self.search([('company_id', '=', company_id.id),
#                                  ('user_id', '=', self.env.user.id)])
#             employee_birthday = leads.filtered(lambda r: r.type == 'birthday')
#             # my_opportunity = leads.filtered(lambda r: r.type == 'opportunity')
#             currency = company_id.currency_id.symbol
#             # expected_revenue = sum(my_opportunity.mapped('expected_revenue'))
#             return {
#                 'total_leads': len(employee_birthday),
#                 # 'total_opportunity': len(my_opportunity),
#                 # 'expected_revenue': expected_revenue,
#                 'currency': currency,
#             }
#
#
class CrmLead(models.Model):
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

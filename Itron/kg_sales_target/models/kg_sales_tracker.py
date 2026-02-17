# -*- coding: utf-8 -*-
import calendar
from datetime import date, datetime, timedelta

from odoo import api, fields, models


class KgSalesTracker(models.TransientModel):
    _name = "kg.sales.tracker"
    _description = "Kg Sales Tracker"
    _order = 'user_id desc'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency', required=True, readonly=True,
        default=lambda self: self.env.company.currency_id)

    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        domain="[('is_salesperson', '=', True)]"
    )

    def get_year(self):
        year = fields.Datetime.now().strftime("%Y")
        return year

    def get_years(self):
        year_list = []
        for i in range(2021, 2050):
            year_list.append((str(i), str(i)))
        return year_list

    month = fields.Selection(
        [
            ("1", "January"),
            ("2", "February"),
            ("3", "March"),
            ("4", "April"),
            ("5", "May"),
            ("6", "June"),
            ("7", "July"),
            ("8", "August"),
            ("9", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Month",
    )
    year = fields.Selection(get_years, string="Year", default=get_year, required=True)
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    tracker_ids = fields.Many2many('kg.sales.tracker.lines')
    report_type = fields.Selection([('yearly', 'Yearly'), ('monthly', 'Monthly')], default='yearly', required=True)

    @api.onchange("month", "year")
    def onchange_month(self):
        self.start_date = self.end_date = False
        if self.month and self.year:
            month_date = date(int(self.year), int(self.month), 1)
            self.start_date = month_date.replace(day=1)
            self.end_date = month_date.replace(
                day=calendar.monthrange(month_date.year, month_date.month)[1]
            )
        elif self.year:
            month_date = date(int(self.year), 1, 1)
            self.start_date = month_date.replace(day=1)
            self.end_date = month_date.replace(month=12, day=31)

    def business_days(start_date, end_date):
        """Inclusive count of weekdays (Mon–Fri) between two dates."""
        total = (end_date - start_date).days + 1
        full_weeks, remainder = divmod(total, 7)
        count = full_weeks * 5
        for i in range(remainder):
            if (start_date + timedelta(days=i)).weekday() < 5:  # 0=Mon ... 6=Sun
                count += 1
        return count

    def action_view_analysis(self):
        if self.user_has_groups('kg_sales_target.kg_sales_tracker_group_manager'):
            if not self.user_id:
                users = self.env['res.users'].sudo().search([('is_salesperson', '=', True)])
            else:
                users = self.user_id
        else:
            users = self.env.user

        today = date.today()

        qualified_stage_id = self.env['crm.stage'].search([('is_qualified', '=', True)], limit=1).id
        opportunity_stage_id = self.env['crm.stage'].search([('is_opportunity', '=', True)], limit=1).id
        proposed_stage_id = self.env['crm.stage'].search([('is_proposed', '=', True)], limit=1).id
        proposal_cold_stage_id = self.env['crm.stage'].search([('is_proposal_cold', '=', True)], limit=1).id
        negotiation_stage_id = self.env['crm.stage'].search([('is_negotiation', '=', True)], limit=1).id
        waiting_stage_id = self.env['crm.stage'].search([('is_po_waiting', '=', True)], limit=1).id
        won_stage_id = self.env['crm.stage'].search([('is_won', '=', True)], limit=1).id

        for usr in users:
            sales_target = self.env['kg.sales.target'].search([('user_id', '=', usr.id), ('company_id', '=', self.company_id.id), ('year', '=', self.year)])
            tot_y2m_target = 0
            if sales_target:
                all_leads = self.env['crm.lead'].search([('user_id', '=', usr.id),('type', '=', 'opportunity')])
                print("all_leads", len(all_leads))
                other_leads = all_leads.filtered(lambda x: x.stage_id.id in [qualified_stage_id, opportunity_stage_id] and x.date_added and self.start_date <= x.date_added.date() <= self.end_date)
                cold_leads = all_leads.filtered(lambda x: x.stage_id.id == proposal_cold_stage_id and x.date_added and x.proposed_by and self.start_date <= x.proposed_by <= self.end_date)
                leads = other_leads + cold_leads
                proposal_leads = all_leads.filtered(lambda x: x.stage_id.id in [proposed_stage_id, negotiation_stage_id, waiting_stage_id] and x.proposed_by and self.start_date <= x.proposed_by <= self.end_date)
                won_leads = all_leads.filtered(lambda x: x.stage_id.id == won_stage_id and x.date_closed and self.start_date <= x.date_closed.date() <= self.end_date)
                start_date = datetime.strptime(str(self.start_date), "%Y-%m-%d")
                end_date = datetime.strptime(str(self.end_date), "%Y-%m-%d")
                current = start_date
                month_vals = {}
                week_vals = {}
                lst_vals = []
                if not self.month:
                    month_dates = []
                    while current <= end_date:
                        year = current.year
                        month = current.month
                        start = datetime(year, month, 1)
                        last_day = calendar.monthrange(year, month)[1]
                        end = datetime(year, month, last_day)
                        month_dates.append((start.date(), end.date()))
                        # move to the first day of the next month
                        current = end + timedelta(days=1)

                    def count_workdays(start, end):
                        day_count = 0
                        current = start
                        while current <= end:
                            if current.weekday() < 5:  # Monday=0, Sunday=6
                                day_count += 1
                            current += timedelta(days=1)
                        week_count = ((end - start).days // 7) + 1
                        return day_count, week_count

                    # Calculate workdays for each month
                    for start, end in month_dates:
                        if start <= today or (start.year == today.year and start.month == today.month):
                            y2m_lead_target = count_workdays(start, end)[0]
                            y2m_prop_target = count_workdays(start, end)[1]
                            lst_vals.append({
                                'user_id': usr.id,
                                'stage': False,
                                'lead_ids': False,
                                'count': 0,
                                'target': 0,
                                'expected_revenue': 0,
                                'y2m_lead_target': y2m_lead_target * sales_target.lead_target,
                                'y2m_proposal_target': y2m_prop_target * sales_target.prop_target,
                                'date': start
                            })

                    # Display the result

                    for i, (s, e) in enumerate(month_dates, start=1):
                        month_leads = leads.filtered(lambda x: s <= x.date_added.date() <= e)
                        month_proposed = proposal_leads.filtered(lambda x: s <= x.proposed_by <= e)
                        month_wons = won_leads.filtered(lambda x: s <= x.date_closed.date() <= e)

                        if not month_wons:
                            tot_month_target = sum(sales_target.monthly_target_lines.filtered(
                                lambda x: x.month == str(s.month) and x.year == self.year).mapped(
                                'target'))
                            y2m_target = 0
                            if s <= today or (s.year == today.year and s.month == today.month):
                                y2m_target = tot_month_target
                                tot_y2m_target += tot_month_target

                            lst_vals.append({
                                'user_id': usr.id,
                                'stage': 'won',
                                'lead_ids': False,
                                'count': 0,
                                'target': 0,
                                'expected_revenue': 0,
                                'total_target': tot_month_target,
                                'y2m_target': y2m_target,
                                'date': s
                            })

                        month_vals['M'+str(i)] = [sum(month_leads.mapped('expected_revenue')), sum(month_proposed.mapped('expected_revenue')), sum(month_wons.mapped('expected_revenue'))]

                else:

                    # Loop through the month week by week
                    week_number = 1
                    while current <= end_date:
                        year = current.year
                        month = current.month

                        # Start of the week
                        week_start = current
                        # End of the week is 6 days later or end of month
                        week_end = min(week_start + timedelta(days=6),
                                       datetime(year, month, calendar.monthrange(year, month)[1]))

                        # Filter and sum values within the week range
                        leads_in_week = leads.filtered(
                            lambda x: week_start.date() <= x.date_added.date() <= week_end.date())
                        proposed_in_week = proposal_leads.filtered(
                            lambda x: week_start.date() <= x.proposed_by <= week_end.date())
                        won_in_week = won_leads.filtered(
                            lambda x: week_start.date() <= x.date_closed.date() <= week_end.date())
                        # if not won_in_week:
                        #     print("won_in_week", won_in_week, week_start.date() , week_end.date())
                        #     tot_week_target = sum(sales_target.monthly_target_lines.filtered(
                        #         lambda x: x.month == str(week_start.date().month) and x.year == self.year).mapped(
                        #         'target')) / 4
                        #     lst_vals.append({
                        #         'user_id': usr.id,
                        #         'stage': 'won',
                        #         'lead_ids': False,
                        #         'count': 1,
                        #         'target': 0,
                        #         'expected_revenue': 0,
                        #         'total_target': 0,
                        #         'date': week_start.date()
                        #     })


                        def count_workdays(week_start, week_end):
                            day_count = 0
                            current = week_start
                            while current <= week_end:
                                if current.weekday() < 5:  # Monday=0, Sunday=6
                                    day_count += 1
                                current += timedelta(days=1)
                            return day_count

                        day_count = count_workdays(week_start, week_end)
                        lst_vals.append({
                            'user_id': usr.id,
                            'stage': False,
                            'lead_ids': False,
                            'count': 0,
                            'target': 0,
                            'expected_revenue': 0,
                            'monthly_leads': len(leads_in_week) + len(proposed_in_week) + len(won_in_week),
                            'monthly_leads_target': day_count,
                            'proposal_achieved': len(proposed_in_week) + len(won_in_week),
                            'y2m_proposal_target': sales_target.prop_target,
                            'monthly_proposal_target': sales_target.prop_target,
                            'date': week_start
                        })

                        week_vals[f'W{week_number}'] = [
                            sum(leads_in_week.mapped('expected_revenue')),
                            sum(proposed_in_week.mapped('expected_revenue')),
                            sum(won_in_week.mapped('expected_revenue'))
                        ]

                        # Move to the next week
                        current = week_end + timedelta(days=1)
                        week_number += 1
                print("leads", leads)
                for l in leads:
                    lst_vals.append({
                        'user_id': usr.id,
                        'stage': 'lead',
                        'lead_ids': [(6, 0, l.ids)],
                        'count': 1,
                        'expected_revenue': l.expected_revenue,
                        'date': l.date_added.date(),
                    })


                for p in proposal_leads:
                    lst_vals.append({
                        'user_id': usr.id,
                        'stage': 'proposal',
                        'lead_ids': [(6, 0, p.ids)],
                        'count': 1,
                        'expected_revenue': p.expected_revenue,
                        'proposal_achieved': 1,
                        'date': p.proposed_by,
                    })
                for w in won_leads:
                    tot_month_target = sum(sales_target.monthly_target_lines.filtered(
                        lambda x: x.month == str(w.date_closed.date().month) and x.year == self.year).mapped(
                        'target'))


                    closed_date = w.date_closed.date()

                    y2m_target = 0
                    tot_current_target = 0
                    if closed_date <= today or (closed_date.year == today.year and closed_date.month == today.month):
                        y2m_target = tot_month_target
                        tot_y2m_target += tot_month_target
                        tot_current_target = sum(won_leads.mapped('expected_revenue'))

                    tot_annual_target = sum(sales_target.target_line_ids.mapped('revenue_head_id').mapped('tot_tar'))
                    lst_vals.append({
                        'user_id': usr.id,
                        'stage': 'won',
                        'lead_ids': [(6, 0, w.ids)],
                        'count': 1,
                        'target': w.expected_revenue,
                        'expected_revenue': w.expected_revenue,
                        'achieved_target_per': (w.expected_revenue/ tot_annual_target) if tot_annual_target else 0,
                        'total_target': tot_month_target,
                        'y2m_target': y2m_target,
                        'proposal_achieved': 1,
                        'tot_current_target': tot_current_target,
                        'y2m_target_per': (tot_current_target/ tot_y2m_target) if tot_y2m_target else 0,
                        'date': w.date_closed.date()
                    })



                self.tracker_ids |= self.env['kg.sales.tracker.lines'].create(lst_vals)
        if not self.month:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Sales Tracker Analysis - '+ str(self.year),
                'res_model': 'kg.sales.tracker.lines',
                'view_mode': 'pivot,tree',
                'context': {'create': False},
                'views': [(self.env.ref('kg_sales_target.kg_sales_tracker_lines_monthly_view_pivot').id, 'pivot'), (self.env.ref('kg_sales_target.kg_sales_tracker_lines_monthly_view_tree').id, 'tree')],
                'domain': [('id', 'in', self.tracker_ids.ids)],
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Sales Tracker Analysis - ' + calendar.month_name[int(self.month)] + ' ' + str(self.year),
                'res_model': 'kg.sales.tracker.lines',
                'view_mode': 'pivot,tree',
                'context': {'create': False},
                'views': [(self.env.ref('kg_sales_target.kg_sales_tracker_lines_weekly_view_pivot').id, 'pivot'), (self.env.ref('kg_sales_target.kg_sales_tracker_lines_weekly_view_tree').id, 'tree')],
                'domain': [('id', 'in', self.tracker_ids.ids)],
                'target': 'current',
            }


class KgSalesTrackerLines(models.TransientModel):
    _name = "kg.sales.tracker.lines"
    _description = "Sales Tracker Analysis"

    user_id = fields.Many2one('res.users', string="Salesperson", readonly=True)
    stage = fields.Selection([('lead', 'Lead'), ('proposal', 'Proposal'), ('won', 'Won')], string="Stage", readonly=True)
    count = fields.Integer('Leads Count', readonly=True)
    date = fields.Date('Date', readonly=True)
    expected_revenue = fields.Monetary('Exp.Revenue', readonly=True)
    target = fields.Monetary('Achieved', readonly=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency', required=True, readonly=True,
        default=lambda self: self.env.company.currency_id)
    y2m_target = fields.Monetary('Y2M Target', readonly=True)
    tot_current_target = fields.Monetary('Y2M Achieved', readonly=True)
    y2m_target_per = fields.Float('Y2M Achieved(%)', readonly=True)
    total_target = fields.Float('Total Target', readonly=True)
    y2m_lead_target = fields.Float('Y2M Leads Target(Count)', readonly=True)
    y2m_proposal_target = fields.Float('Y2M Proposal Target(Count)', readonly=True)
    monthly_proposal_target = fields.Float('Proposal Target(Count)', readonly=True)
    monthly_leads = fields.Float('Leads Count', readonly=True)
    monthly_leads_target = fields.Float('Leads Target(Count)', readonly=True)
    y2m_lead_achieved = fields.Float('Y2M Leads Achieved(%)', readonly=True)
    proposal_achieved = fields.Float('Proposal Achieved(Count)', readonly=True)
    achieved_target_per = fields.Float('Achieved(%)', readonly=True)
    lead_ids = fields.Many2many('crm.lead',  string='Leads')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)

    def view_leads(self):
        return {
                'type': 'ir.actions.act_window',
                'name': 'Leads',
                'res_model': 'crm.lead',
                'view_mode': 'tree,form',
                'context': {'create': False},
                'domain': [('id', 'in', self.lead_ids.ids)],
                'target': 'new',
            }








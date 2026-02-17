# -*- coding: utf-8 -*-

from odoo import api, models


class ReportTimesheet(models.AbstractModel):
    """Create an Abstract Class for report data to pass to the templates"""
    _name = 'report.kg_itron_timesheet.report_timesheet_employee'
    _description = 'Timesheet Report'

    def get_timesheets(self, docs):
        """Fetch timesheets based on filters: user, dates, and selected projects."""
        records = []
        total = 0.0

        # Iterate over each selected employee
        for user in docs.user_id:
            domain = [('user_id', '=', user.id)]

            # Add date filters
            if docs.from_date:
                domain.append(('date', '>=', docs.from_date))
            if docs.to_date:
                domain.append(('date', '<=', docs.to_date))

            # Add project filter if projects are selected in the wizard
            if docs.project_id:
                domain.append(('project_id', 'in', docs.project_id.ids))

            # Search timesheets based on the constructed domain
            timesheets = self.env['account.analytic.line'].search(domain)

            # Process timesheets for the current user
            for rec in timesheets:
                vals = {
                    'employee': rec.employee_id.name,
                    'project': rec.project_id.name,
                    'task': rec.task_id.name,
                    'description': rec.name,
                    'date_start': rec.date_start,
                    'date_end': rec.date_end,
                    'user': rec.user_id.partner_id.name,
                    'duration': rec.unit_amount,
                    'date': rec.date,
                }
                total += rec.unit_amount
                records.append(vals)

        # total = round(total, 2)
        return [records, total]

    @api.model
    def _get_report_values(self, docids, data=None):
        print("ssssssssssssssssssssssssssssss")
        """Fetch report values and pass them to the template."""
        docs = self.env['timesheet.report'].browse(self.env.context.get('active_id'))
        identification = []

        for rec in self.env['hr.employee'].search([('user_id', '=', docs.employee_id.id)]):
            if rec:
                identification.append({'id': rec.id, 'name': rec.name})

        # Fetch the timesheets with the applied filters
        timesheets = self.get_timesheets(docs)
        # project_names = ", ".join([project.name for project in docs.project_ids])
        # print("project_names",project_names)
        # Company information
        company_id = self.env['res.company'].search([('name', '=', docs.employee_id.company_id.name)])
        print("company_id",company_id)

        # Define period
        period = None
        if docs.from_date and docs.to_date:
            period = f"From {docs.from_date.strftime('%d/%m/%Y')} To {docs.to_date.strftime('%d/%m/%Y')}"
        elif docs.from_date:
            period = f"From {docs.from_date.strftime('%d/%m/%Y')}"
        elif docs.to_date:
            period = f"To {docs.to_date.strftime('%d/%m/%Y')}"

        # Return values to be rendered in the report
        if len(identification) > 1:
            return {
                'doc_ids': self.ids,
                'docs': docs,
                'timesheets': timesheets[0],
                'total': timesheets[1],
                'company': company_id,
                'identification': identification,
                'period': period,
                'data': data,
                'project': docs.project_id,
                'employee': docs.employee_id,

            }
        else:
            return {
                'doc_ids': self.ids,
                'docs': docs,
                'timesheets': timesheets[0],
                'total': timesheets[1],
                'identification': identification,
                'company': company_id,
                'period': period,
                'project': docs.project_id,
                'employee': docs.employee_id,

            }

import base64
import logging
from datetime import date

import werkzeug

import odoo.http as http
from odoo.http import request

_logger = logging.getLogger(__name__)


class HelpdeskTicketController(http.Controller):
    @http.route("/ticket/close", type="http", auth="user")
    def support_ticket_close(self, **kw):
        """Close the support ticket"""
        values = {}
        for field_name, field_value in kw.items():
            if field_name.endswith("_id"):
                values[field_name] = int(field_value)
            else:
                values[field_name] = field_value
        ticket = (http.request.env["helpdesk.ticket"].sudo().search([("id", "=", values["ticket_id"])]))
        ticket.stage_id = values.get("stage_id")
        return werkzeug.utils.redirect("/my/ticket/" + str(ticket.id))

    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        categories = http.request.env["helpdesk.ticket.category"].sudo().search(
            [('user_ids', 'in', [http.request.env.user.id]), ('active', '=', True)])
        applications = http.request.env["helpdesk.ticket.application"].sudo().search(
            [('user_ids', 'in', [http.request.env.user.id]), ('active', '=', True)])
        amc_records = request.env['project.contract.request.amc'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('date_start', '<=', date.today()),
            ('date_end', '>=', date.today()),
        ])
        amc_success_pack = request.env['pack.projects'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('start_date', '<=', date.today()),
            ('end_date', '>=', date.today()),
            ('stages', '=', 'in_progress')
        ])
        free_support = request.env['project.contract.request.free.support'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('state', '=', 'active'),
        ])

        has_amc_success_pack = bool(amc_success_pack)
        has_free_support = bool(free_support)

        total_enhancement_spent_hrs = sum(amc_records.mapped('enhancement_spent_hrs'))
        total_enhancement_hrs = sum(amc_records.mapped('enhancement_hrs'))
        email = http.request.env.user.email
        name = http.request.env.user.name
        restrict_ticket = any(amc.restrict_ticket for amc in amc_records)
        return http.request.render("helpdesk_mgmt.portal_create_ticket",
                                   {"categories": categories,"enhancement_hrs": total_enhancement_hrs,"enhancement_spent_hrs":total_enhancement_spent_hrs,"applications": applications, "email": email,
                                    "name": name,"restrict_ticket":restrict_ticket,"has_amc_success_pack":has_amc_success_pack,"has_free_support":has_free_support})

    def format_hours_minutes(self, float_hours):
        """Convert float hours to 'X hr Y min'."""
        hours = int(float_hours)
        minutes = int(round((float_hours - hours) * 60))
        return f"{hours} hr {minutes} min"

    @http.route("/ticket/planned_hours", type="http", auth="user", website=True)
    def ticket_planned_hours(self, **kw):
        amc_records = request.env['project.contract.request.amc'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('date_start', '<=', date.today()),
            ('date_end', '>=', date.today()),
        ])
        ProjectTask = request.env['project.task']
        tickets_data = []

        for amc in amc_records:
            period_data = []
            today = date.today()

            for idx, period in enumerate(amc.engagement_period_ids, start=1):
                tickets = ProjectTask.sudo().search([
                    ('project_id', '=', amc.project_id.id),
                    ('date_start', '>=', period.period_start_date),
                    ('date_deadline', '<=', period.period_end_date)
                ])
                spent_hours = sum(tickets.mapped('allocated_hours'))

                period_data.append({
                    'index': idx,
                    'start': period.period_start_date,
                    'end': period.period_end_date,
                    'spent_hours': self.format_hours_minutes(spent_hours),
                    'is_current': period.period_start_date <= today <= period.period_end_date if period.period_end_date and period.period_start_date else False,
                })

            tickets_data.append({
                'amc': amc,
                'planned_hours': self.format_hours_minutes(amc.planned_hrs),
                'support_hours': self.format_hours_minutes(amc.support_hrs),
                'enhancement_hrs': self.format_hours_minutes(amc.enhancement_hrs),
                'support_spent_hours': self.format_hours_minutes(amc.support_spent_hrs),
                'enhancement_spent_hours': self.format_hours_minutes(amc.enhancement_spent_hrs),
                'spent_hours': self.format_hours_minutes(
                    sum(ProjectTask.sudo().search([
                        ('project_id', '=', amc.project_id.id),
                        ('date_start', '>=', amc.date_start),
                        ('date_deadline', '<=', amc.date_end)
                    ]).mapped('allocated_hours'))
                ),
                'periods': period_data,
            })

        return request.render("helpdesk_mgmt.portal_amc_hours", {
            'tickets_data': tickets_data,
            'user': request.env.user,
        })

    @http.route("/ticket/contracts", type="http", auth="user", website=True)
    def ticket_contracts(self, **kw):
        today = date.today()
        amc_records = request.env['project.contract.request.amc'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
        ])
        free_supp_records = request.env['project.contract.request.free.support'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
        ])
        success_packs_records = request.env['pack.projects'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
        ])

        amc_data = [{
            'record': amc,
            'is_current': amc.date_start <= today <= amc.date_end,
        } for amc in amc_records]

        success_pack_data = [{
            'record': fs,
            'is_current': fs.start_date <= today <= fs.end_date,
        } for fs in success_packs_records]

        free_support_data = [{
            'record': fs,
            'is_current': fs.date_start <= today <= fs.date_end,
        } for fs in free_supp_records]

        return request.render("helpdesk_mgmt.portal_contracts_view", {
            'amc_data': amc_data,
            'free_support_data': free_support_data,
            'success_pack_data': success_pack_data,
            'user': request.env.user,
        })


    @http.route("/submitted/ticket", type="http", auth="user", website=True, csrf=True)
    def submit_ticket(self, **kw):
        category = http.request.env["helpdesk.ticket.category"].sudo().browse(int(kw.get("category")))
        application = http.request.env["helpdesk.ticket.application"].sudo().browse(int(kw.get("application")))
        vals = {
            "company_id": category.company_id.id or http.request.env.user.company_id.id,
            "category_id": category.id,
            "application_id": application.id,
            "description": kw.get("description"),
            "priority": kw.get("priority"),
            "name": kw.get("subject"),
            "attachment_ids": False,
            "channel_id": request.env["helpdesk.ticket.channel"].sudo().search([("name", "=", "Web")]).id,
            "partner_id": request.env.user.partner_id.id,
            "partner_name": request.env.user.partner_id.name,
            "partner_email": request.env.user.partner_id.email,
        }
        new_ticket = request.env["helpdesk.ticket"].sudo().create(vals)
        new_ticket.message_subscribe(partner_ids=request.env.user.partner_id.ids)
        if kw.get("attachment[]"):
            for c_file in request.httprequest.files.getlist("attachment[]"):
                data = c_file.read()
                if c_file.filename:
                    request.env["ir.attachment"].sudo().create(
                        {
                            "name": c_file.filename,
                            "datas": base64.b64encode(data),
                            "res_model": "helpdesk.ticket",
                            "res_id": new_ticket.id,
                        }
                    )
        return werkzeug.utils.redirect("/my/ticket/%s" % new_ticket.id)



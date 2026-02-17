from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessError


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    def get_helpdesk_ticket_data(self):
        print('success')
        helpdesk_ids = self.env['helpdesk.ticket'].sudo().search([])
        user = self.env.user
        user_ids = []
        is_admin = user.has_group('base.group_system')
        is_heldesk_user = user.has_group('helpdesk_mgmt.group_helpdesk_user_own')
        is_heldesk_manager = user.has_group('helpdesk_mgmt.group_helpdesk_manager')
        is_heldesk_user_1 = user.has_group('helpdesk_mgmt.group_helpdesk_user')

        domain = []
        teams = self.env['project.team'].sudo().search([('timesheet_user_ids', '=', user.id)])
        companies = self.env.user.company_ids
        company_data = [{"id": company.id, "name": company.name} for company in companies]
        is_cto = user.has_group('kg_timeoff_dashboard.group_admin_india_dashboard')

        if is_cto and not is_admin:
            # CTO: all users in their company
            print("CTO logged in")
            user_ids = self.env['res.users'].sudo().search([
                ('company_id', '=', self.env.company.id)
            ])
            domain.append(('user_id', 'in', user_ids.ids))

        elif not is_admin and not is_heldesk_user:
            user_ids = teams.mapped('employee_ids').sorted('name')
            domain.append(('user_id', 'in', user_ids.ids))
        elif not is_admin and is_heldesk_user_1 and not is_heldesk_manager:
            print(is_heldesk_user_1, "is_heldesk_user_1")

            team_lead_group = self.env.ref('project.group_project_manager')
            team_lead_users = self.env['res.users'].search([
                ('groups_id', 'in', team_lead_group.id),
                ('company_id', '=', user.company_id.id)
            ])

            user_ids = team_lead_users | user

            domain.append(('user_ids', 'in', user_ids.ids))
        elif not is_admin and is_heldesk_user and not is_heldesk_manager:
            print(is_heldesk_user, "not magerxxxxxxxxxxxxx")

            user_ids = user
            domain.append(('user_ids', '=', user.id))
        elif is_heldesk_manager:
            helpdesk_ids = helpdesk_ids.filtered(lambda x: x.company_id.id in self.env.user.company_ids.ids)
            user_ids = helpdesk_ids.mapped('user_id').sorted('name')

        vals = []
        assignee_list = []
        usr = helpdesk_ids.filtered(lambda x: x.user_id and x.user_id in user_ids)

        for users in usr.mapped('user_id'):
            if users not in assignee_list:
                assignee_list.append(users)
                employee = {'id': users.id, 'name': users.name,
                            'open': 0, 'inprogress': 0, 'held': 0, 'closed': 0,'returned': 0,'cr':0,
                            'total': 0, 'ticket_ids': [], 'uat': 0,
                            # 'customer':''
                            }
                vals.append(employee)
        helpdesk_teams = self.env['helpdesk.ticket.team'].sudo().search([('user_ids', 'in', user_ids.ids)])

        # unassigned_tickets = helpdesk_ids.filtered(lambda x: not x.user_id and x.company_id.id in self.env.user.company_ids.ids and x.team_id in helpdesk_teams )
        unassigned_tickets = helpdesk_ids.filtered(lambda
                                                       x: not x.user_id and x.company_id.id in self.env.user.company_ids.ids and x.team_id in helpdesk_teams)
        company_unassigned_map = {}
        for ticket in unassigned_tickets:
            company_id = ticket.company_id.id
            if company_id not in company_unassigned_map:
                company_unassigned_map[company_id] = []
            company_unassigned_map[company_id].append(ticket)

        count = -1

        for company_id, tickets in company_unassigned_map.items():
            open_tickets = [t.id for t in tickets if t.stage_id.name == 'Open']
            inprogress_tickets = [t.id for t in tickets if t.stage_id.name == 'In Progress']

            held_tickets = [t.id for t in tickets if t.stage_id.name == 'Hold']

            closed_tickets = [t.id for t in tickets if t.stage_id.name == 'Closed']

            uat_tickets = [t.id for t in tickets if t.stage_id.name == 'UAT']
            cr_tickets = [t.id for t in tickets if t.stage_id.name == 'Change Request']
            returned_tickets = [t.id for t in tickets if t.stage_id.name == 'Returned']


            company = self.env['res.company'].browse(company_id)

            unassigned_employee = {
                'id': count,
                'name': f'Unassigned - {company.name}',
                'company_id': company.id,
                'company': company.name,
                'open': len(open_tickets),
                'inprogress': len(inprogress_tickets),
                'uat': len(uat_tickets),
                'held': len(held_tickets),
                'closed': len(closed_tickets),
                'cr': len(cr_tickets),
                'returned': len(returned_tickets),
                'total': len(tickets),
                # 'customer': '',
                'ticket_ids': {
                    'open': open_tickets,
                    'inprogress': inprogress_tickets,
                    'uat': uat_tickets,
                    'cr': cr_tickets,
                    'held': held_tickets,
                    'returned': returned_tickets,
                    'closed': closed_tickets,
                    'company': company.name,
                    'company_id': company.id
                }
            }
            count -= 1
            vals.append(unassigned_employee)

        # Now loop over the assignee list and calculate ticket counts
        for ass_usr in assignee_list:
            helpdesk_ticket_ids = helpdesk_ids.filtered(lambda x: x.user_id and x.user_id == ass_usr)

            ticket_count = len(helpdesk_ticket_ids)
            open_ticket_ids = helpdesk_ticket_ids.filtered(lambda x: x.stage_id.name == 'Open')
            open_ticket_count = len(open_ticket_ids)

            inprogress_ticket_ids = helpdesk_ticket_ids.filtered(lambda x: x.stage_id.name == 'In Progress')
            inprogress_ticket_count = len(inprogress_ticket_ids)

            uat_ticket_ids = helpdesk_ticket_ids.filtered(lambda x: x.stage_id.name == 'UAT')
            uat_ticket_count = len(uat_ticket_ids)

            held_ticket_ids = helpdesk_ticket_ids.filtered(lambda x: x.stage_id.name == 'Hold')
            held_ticket_count = len(held_ticket_ids)

            cr_ticket_ids = helpdesk_ticket_ids.filtered(lambda x: x.stage_id.name == 'Change Request')
            cr_ticket_count = len(cr_ticket_ids)
            print("cr_ticket_count",cr_ticket_count)

            returned_ticket_ids = helpdesk_ticket_ids.filtered(lambda x: x.stage_id.name == 'Returned')
            returned_ticket_count = len(returned_ticket_ids)

            closed_ticket_ids = helpdesk_ticket_ids.filtered(lambda x: x.stage_id.name == 'Closed')
            closed_ticket_count = len(closed_ticket_ids)

            for item in vals:
                if item.get('id') == ass_usr.id:
                    item['open'] = open_ticket_count
                    item['inprogress'] = inprogress_ticket_count
                    item['uat'] = uat_ticket_count
                    item['held'] = held_ticket_count
                    item['returned'] = returned_ticket_count
                    item['cr'] = cr_ticket_count
                    item['closed'] = closed_ticket_count
                    item['company'] = ass_usr.company_id.name
                    item['company_id'] = ass_usr.company_id.id
                    item['ticket_ids'] = {
                        'open': open_ticket_ids.ids,
                        'inprogress': inprogress_ticket_ids.ids,
                        'uat': uat_ticket_ids.ids,
                        'held': held_ticket_ids.ids,
                        'cr': cr_ticket_ids.ids,
                        'returned': returned_ticket_ids.ids,
                        'closed': closed_ticket_ids.ids,
                        'company': ass_usr.company_id.name,
                        'company_id': ass_usr.company_id.id
                    }

        return {'vals': vals, 'is_admin': is_admin, 'is_heldesk_manager': is_heldesk_manager,
                'company_data': company_data}
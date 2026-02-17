# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket', readonly=True, copy=False)
    ticket_count = fields.Integer(string='Ticket Count', readonly=True, copy=False, compute='compute_ticket_count')

    def action_open_ticket(self):
        """ Smart button to display created ticket. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Ticket's",
            'view_mode': 'tree,form',
            'res_model': 'helpdesk.ticket',
            'context': "{'create':False}",
            'domain': [('id', '=', self.ticket_id.id)]
        }

    def compute_ticket_count(self):
        """ Compute ticket count in smart tab """
        for rec in self:
            rec.ticket_count = rec.ticket_id.search_count([('tasks_ids', 'in', rec.ids)])

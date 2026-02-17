# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from datetime import date, datetime, timedelta



class ProjectContractRequestFreeSupport(models.Model):
    _name = 'project.contract.request.free.support'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Free Support"

    name = fields.Char('Name', default=lambda self: _('New'), copy=False, )
    contract_type = fields.Selection([('free', 'Free Support')], 'Contract Type',
                                     default='free')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)

    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    po_no = fields.Char('Contract Number', copy=False, readonly=True, index=True, default=lambda self: _(''))

    date_start = fields.Date('Start Date', default=fields.Date.context_today, copy=False)
    date_end = fields.Date('End Date')
    project_id = fields.Many2one('project.project', 'Project', copy=False)
    planned_days = fields.Integer(String='Planned Days', copy=False)
    description = fields.Char(string='Description', copy=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    allowed_company_ids = fields.Many2many('res.company',string='Visible Companies', default=lambda self: self.env.company.ids)


    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('hold', 'Hold'),
    ], string='Status', default='draft', tracking=True)

    ribbon_status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('hold', 'Hold'),
    ], string="Ribbon Status", compute="_compute_ribbon_status", store=True, default="draft")
    sale_id = fields.Many2one('sale.order', string="Sale Order")

    @api.model_create_multi
    def create(self, vals_list):
        """ Create a sequence for the Free Support model """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('contract.reference.free.support')
                vals['name'] = sequence
            if vals.get('po_no', _('')) == _(''):
                sequence = self.env['ir.sequence'].next_by_code('contract.number.free.support')
                vals['po_no'] = sequence
        return super().create(vals_list)

    @api.onchange('date_end', 'date_start')
    def onchange_date(self):
        """ Set state according to date """
        today = fields.Date.today()
        for rec in self:
            if rec.date_end and rec.date_start <= today <= rec.date_end:
                rec.write({
                    'state': 'active'
                })
            else:
                rec.write({
                    'state': 'draft'
                })

    def cron_action_contract_state(self):
        """ cron action to change contract stage """
        today = fields.Date.today()
        for rec in self.search([]):
            if rec.date_start and rec.date_start <= today <= rec.date_end and rec.state != 'hold':
                rec.write({
                    'state': 'active'
                })
            if rec.date_end and rec.date_end <= today:
                rec.write({
                    'state': 'expired'
                })

    @api.depends('state', 'date_start', 'date_end')
    def _compute_ribbon_status(self):
        """ Compute function for value of ribbon_status according to state """
        for rec in self:
            if rec.state == 'draft':
                rec.write({'ribbon_status': 'draft'})
            elif rec.state == 'active':
                rec.write({'ribbon_status': 'active'})
            elif rec.state == 'hold':
                rec.write({'ribbon_status': 'hold'})
            else:
                rec.write({'ribbon_status': 'expired'})

    def set_to_hold(self):
        """ Button action to set the state to hold """
        for rec in self:
            rec.write({
                'state': 'hold',
            })

    def set_to_draft(self):
        """ Button action to set the state to draft """
        for rec in self:
            rec.write({
                'state': 'draft',
            })

    def get_free_support_data(self):
        print("get_free_support_data")

        today = date.today()
        domain = [
            # ('date_start', '<=', today),
        ]

        free_contracts = self.env['project.contract.request.free.support'].search(domain)
        customers = [{"id": customer.id, "name": customer.name} for customer in
                     free_contracts.sudo().mapped('partner_id')]
        used_states = list(set(free_contracts.mapped('state')))
        ribbon_status= list(set(free_contracts.mapped('ribbon_status')))
        print("rebion_status",ribbon_status)
        ribbon_status_selection = dict(self._fields['ribbon_status'].selection)
        ribbon_status_val = [(key, ribbon_status_selection[key]) for key in ribbon_status if
                             key in ribbon_status_selection]
        print("rebion_status_val",ribbon_status_val)
        user_company_ids = set(self.env.user.company_ids.ids)
        free_data = []

        # Process all contracts without company filtering
        for free in free_contracts:
            free_data.append({
                'id': free.id,
                'contract_no': free.po_no or '',
                'project_id': free.project_id.name or '',
                'customer_id': free.partner_id.id,
                'customer_name': free.partner_id.name,
                'date_start': free.date_start.strftime('%d/%m/%Y') if free.date_start else '',
                'date_end': free.date_end.strftime('%d/%m/%Y') if free.date_end else '',
                'contract_type': dict(free._fields['contract_type'].selection).get(free.contract_type),
                'planned_days': free.planned_days or 0,
                'description': free.description or '',
                'ribbon_status': dict(free._fields['ribbon_status'].selection).get(free.ribbon_status),
                'ribbon_status_key': free.ribbon_status,
            })

        return {
            'free_contract': free_data,
            'customers': customers,
            'ribbon_status_val': ribbon_status_val
        }








    # def get_free_support_data(self):
    #     print("get_free_support_data")
    #
    #     today = date.today()
    #     domain = [
    #         # ('date_start', '<=', today),
    #     ]
    #
    #     free_contracts = self.env['project.contract.request.free.support'].sudo().search(domain)
    #     customers = [{"id": customer.id, "name": customer.name} for customer in
    #                  free_contracts.sudo().mapped('partner_id')]
    #     # used_states = list(set(free_contracts.mapped('state')))
    #     # full_state_selection = dict(self.env['project.contract.request.free.support']._fields['state'].selection)
    #     # state_val = [(key, full_state_selection[key]) for key in used_states if key in full_state_selection]
    #     # rebion_statuse = list(set(free_contracts.mapped('rebion_status')))
    #     # rebion_statu_selection = dict(self._fields['rebion_status'].selection)
    #     # rebion_status_val = [(key, rebion_statu_selection[key]) for key in rebion_statuse if
    #     #                      key in rebion_statu_selection]
    #     user_company_ids = set(self.env.user.company_ids.ids)
    #     print(f"User company IDs: {user_company_ids}")
    #
    #     user_company_ids = set(self.env.user.company_ids.ids)
    #     free_data = []
    #     for free in free_contracts.filtered(
    #             lambda amc: any(comp.id in user_company_ids for comp in amc.project_id.company_ids)
    #     ):
    #         free_data.append({
    #             'id': free.id,
    #             'contract_no': free.po_no or '',
    #             'project_id': free.project_id.name,
    #             'customer_id': free.partner_id.id,
    #             'customer_name': free.partner_id.name,
    #             'date_start': free.date_start.strftime('%d/%m/%Y') if free.date_start else '',
    #             'date_end': free.date_end.strftime('%d/%m/%Y') if free.date_end else '',
    #             'contract_type': dict(free._fields['contract_type'].selection).get(free.contract_type),
    #             # 'state_key': free.state,
    #             # 'rebion_status': dict(free._fields['rebion_status'].selection).get(free.rebion_status),
    #             # 'rebion_status_key': free.rebion_status,
    #             'planned_days': free.planned_days or 0,
    #             'description': free.description or '',
    #         })
    #         print("free_datafree_data",free_data, len(free_contracts))
    #
    #     return {
    #         'free_contract': free_data,
    #         'customers': customers,
    #         # 'state_val': list(state_val),
    #         # 'rebion_status_val': rebion_status_val,
    #     }

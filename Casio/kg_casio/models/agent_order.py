# -*- coding: utf-8 -*-
# from odoo.exceptions import Warning

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, date
import random
import string

class AgentOrder(models.Model):
	_name = 'agent.order'

	name = fields.Char('Agent')
	agent_name = fields.Char('Agent Name',required=True)
	order_no = fields.Integer('Order No',required=True)
	partner_id = fields.Many2one('res.partner','Customer')

	@api.model
	def create(self,vals):
		vals['name'] = str(vals['order_no']) + ' ' + vals['agent_name']
		return super(AgentOrder, self).create(vals)


	@api.onchange('partner_id')
	def change_partner(self):
		count_agents = self.env['agent.order'].search_count([('partner_id', '=', self.partner_id.id)]) 
		if count_agents :
			self.order_no = count_agents + 1  
		else:
			self.order_no = 1	 

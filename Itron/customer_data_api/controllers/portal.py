# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import conf, http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from odoo.addons.web.controllers.main import HomeStaticTemplateHelpers
from odoo.addons.portal.controllers.portal import pager


class PortalOpportunity(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'opportunity_count' in counters:
            values['opportunity_count'] = request.env['crm.lead'].search_count([])
        return values

    @http.route(['/my/oppurtunity','/my/oppurtunity/page/<int:page>'], type='http', auth="user",website=True)
    def PortalOpportunityListView(self, page = 1, sortby='id',search="",search_in="All",groupby="none", **kw):
        if not groupby:
            groupby = 'none'
        sorted_list = {
            'id': {'label': 'Latest', "order": 'id desc'},
             'name': {'label': ' Opportunity Name', 'order': 'name'},
             'email_from': {'label': 'Email', 'order': 'email_from'},
             'mobile': {'label': 'Mobile', 'order': 'mobile'},
             'contact_name': {'label': 'Contact Name', 'order': 'contact_name'},
             'partner_name': {'label': 'Company Name', 'order': 'partner_name'},
             'team_id': {'label': 'Sales Team', 'order': 'team_id'},
             'user_id': {'label': 'Salesperson', 'order': 'user_id'},
             'type': {'label': 'Type', 'order': 'type'}
        }
        search_list = {
            'All' : {'label': 'All', 'input' : 'All','domain':[]},
            'Name' : {'label': 'Search by Opportunity Name', 'input' : 'Name','domain':[('name', 'ilike', search)]},
            'Email' : {'label': 'Search by Email', 'input' : 'Email','domain':[('email_from', 'ilike', search)]},
            'Mobile' : {'label': 'Search by Mobile', 'input' : 'Mobile','domain':[('mobile', 'ilike', search)]},
            'Contact Name' : {'label': 'Search by Contact Name', 'input' : 'Contact Name','domain':[('contact_name', 'ilike', search)]},
            'Company Name' : {'label': 'Search by Company Name', 'input' : 'Company Name','domain':[('partner_name', 'ilike', search)]},
            'Sales Team' : {'label': 'Search by Sales Team', 'input' : 'Sales Team','domain':[('team_id.name', 'ilike', search)]},
            'Salesperson' : {'label': 'Search by Salesperson', 'input' : 'Salesperson','domain':[('user_id.name', 'ilike', search)]},
            'Type' : {'label': 'Search by Type', 'input' : 'Type','domain':[('type', 'ilike', search)]},
        }
        groupby_list = {
            'none':{'input': 'none','label': _("None"), "order": 1},
            'team_id':{'input': 'team_id','label': _("Sales Team"), "order": 1},
            'user_id':{'input': 'user_id','label': _("Salesperson"), "order": 1},
            'type':{'input': 'type','label': _("Type"), "order": 1},

        }
        opport_group_by = groupby_list.get(groupby,{})
        search_domain = search_list[search_in]['domain']
        default_order_by = sorted_list[sortby]['order']
        if groupby in ("team_id","user_id","type"):
            opport_group_by = opport_group_by.get("input")
            default_order_by = opport_group_by+","+default_order_by
        else:
            opport_group_by = ''
        opports_obj = request.env['crm.lead']
        opprt_url = '/my/oppurtunity'
        total_opportunities = opports_obj.search_count(search_domain)
        page_detail = pager(url="/my/oppurtunity",
                            total=total_opportunities,
                            page=page,
                            url_args={'search_in': search_in, 'search': search, 'sortby': sortby,'groupby': groupby,},
                            step=20)
        opports = opports_obj.sudo().search(search_domain,limit=20, offset = page_detail['offset'],order=default_order_by)
        if opport_group_by:
            opports_group_list = [{opport_group_by:k, 'opports':opports_obj.concat(*g)} for k, g in groupbyelem(opports,itemgetter(opport_group_by))]
        else:
            opports_group_list = [{'opports':opports}]

        vals = {
                'opports':opports,
                'pager':page_detail,
                # 'opports':opports,
                'group_opports':opports_group_list,
                'page_name':'opports_list_view',
                'default_url':opprt_url,
                'sortby':sortby,
                'groupby':groupby,
                'searchbar_sortings':sorted_list,
                'search_in': search_in,
                'searchbar_inputs':search_list,
                'searchbar_groupby':groupby_list,
                'search': search,
                }
        return request.render("customer_data_api.wb_opportunity_list_view_portal",vals)

    @http.route(['/my/oppurtunity/<model("crm.lead"):opportunity_id>'], type='http', auth="public", website=True)
    def PortalOpportunityFormView(self, opportunity_id, **kw):
        vals = {'opport': opportunity_id,
                'page_name': 'opports_form_view',
                }
        opport_records = request.env['crm.lead'].search([])
        opport_ids = opport_records.ids
        opport_index = opport_ids.index(opportunity_id.id)
        if opport_index !=0 and opport_ids[opport_index - 1]:
            vals['prev_record'] = '/my/oppurtunity/{}'.format(opport_ids[opport_index-1])
        if opport_index < len(opport_ids) -1 and opport_ids[opport_index+1]:
            vals['next_record'] = '/my/oppurtunity/{}'.format(opport_ids[opport_index+1])
        return request.render("customer_data_api.wb_opportunity_form_view_portal",vals)

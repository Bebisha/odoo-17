# -*- coding: utf-8 -*-
import werkzeug
import json
import base64

import odoo.http as http
from odoo.http import request

# from odoo.addons.website.models.website import slug

class SurveyLeadController(http.Controller):

        
    @http.route('/survey/partner/<survey_id>', type="http", auth="public", website=True)
    def survey_partner(self, survey_id, **kw):
        """Associate to partner from email"""
 
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
            my_partner = request.env['res.partner'].sudo().search([('email','=',values['email'])])[0]

            survey_answer = request.env['survey.user_input'].sudo().search([('token','=',values['token'] )])
            survey_answer.partner_id = my_partner.id

            #Add the new partner to a campaign
            for act in survey_answer.survey_id.campaign_id.activity_ids:
                if act.start:
                    wi = request.env['marketing.campaign.workitem'].sudo().create({'campaign_id': survey_answer.survey_id.campaign_id.id, 'activity_id': act.id, 'res_id': my_partner.id})
                    wi.process()
                    request.env['mail.mail'].process_email_queue()
        return werkzeug.utils.redirect("/")
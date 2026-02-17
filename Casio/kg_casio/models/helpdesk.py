# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
from datetime import date, datetime
import json
from langdetect import detect_langs, DetectorFactory
# from langdetect import detect


# DetectorFactory.seed = 0

_logger = logging.getLogger(__name__)


class HelpdeskStageTemplates(models.Model):
    _name = 'helpdesk.stage.templates'
    _description = 'Helpdesk Stage Templates'

    name = fields.Char('Description')
    kg_pre_lang = fields.Selection(
        [('english', 'English(الإنجليزية)'), ('arabic', 'Arabic(عربى)'), ('french', 'French(فرنسي)')],
        'Language', default='english')
    template_id = fields.Many2one('mail.template', 'Email Template', domain="[('model', '=', 'helpdesk.ticket')]")
    stage_id = fields.Many2one('helpdesk.stage', 'Stage')

    _sql_constraints = [
        ('lang_uniq', 'unique(kg_pre_lang,stage_id)', 'One template per language !'),
    ]


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'
    lang_templates = fields.One2many('helpdesk.stage.templates', 'stage_id', 'Templates')


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    manager_id = fields.Many2one('res.users', 'Manager')
    marketing_team_ids = fields.Many2many('res.users', relation='team_marketing_rel', string='Marketing Team Ids')


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # def _track_template(self, changes):
    #     res = super(HelpdeskTicket, self)._track_template(changes)
    #
    #     if 'stage_id' in changes and self.stage_id.template_id:
    #         template = self.env['helpdesk.stage.templates'].search([('stage_id','=',self.stage_id.id),('kg_pre_lang','=',self.partner_id.kg_pre_lang)]) or se.stage_id.template_id
    #
    #         res['stage_id'] = (template, {
    #             'auto_delete_message': True,
    #             'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'),
    #             'email_layout_xmlid': 'mail.mail_notification_light'
    #         })
    #     return res
    # def create_ticket(self):
    #     create_ticket_values = {
    #         'name': 'direct',
    #         'form_type': 'ec_form',
    #     }
    #     ticket = self.env['helpdesk.ticket'].sudo().create(create_ticket_values)

    @api.model
    def create_ticket_from_ec_rtn_form(self, values):
        ticket = self.env['helpdesk.ticket']
        try:
            _logger.info(str(values))
            values = json.loads(values)
            if values.get('topic'):
                if not isinstance(values['topic'], int):
                    topic_search = self.env['kg.topic'].sudo().search([('name', '=', values['topic'])], limit=1)
                    if topic_search:
                        topic = topic_search.id
                    else:
                        new_topic_id = self.env['kg.topic'].sudo().create({'name': values['topic']})
                        topic = new_topic_id.id
            if values.get('customer'):
                if not isinstance(values['customer'], int):
                    customer_search = self.env['res.partner'].sudo().search([('email', '=', values['email'])], limit=1)
                    if customer_search:
                        customer = customer_search
                    else:
                        new_cust_id = self.env['res.partner'].sudo().create(
                            {'name': values['customer'], 'email': values['email'], 'city': values['city']})
                        customer = new_cust_id
            create_ticket_values = {
                'partner_id': customer.id,
                'name': values.get('subject'),
                'form_type': values.get('form_type'),
                'partner_email': customer.email,
                'city_text': customer.city,
                'mob': values.get('mobile'),
                'topic': topic,
                'subject': values.get('subject'),
                'product_opened': values.get('product_opened'),
                'description': values.get('refund_reason')
            }
            ticket = self.env['helpdesk.ticket'].sudo().create(create_ticket_values)
            if len(ticket) == 1:
                return {"status": '00', "message": "Successfully created Ticket"}
            else:
                return {"status": '01', "message": "Something went wrong!!!!!"}
        except Exception as e:
            _logger.info(str(e))
            if len(ticket) == 1:
                return {"status": '00', "message": "Successfully created Ticket"}
            else:
                return {"status": '01', "message": "Something went wrong : %s" % str(e)}

    @api.model
    def create_ticket_from_ec_form(self, values):
        ticket = self.env['helpdesk.ticket']
        uae_id = self.env.ref('base.ae').id
        try:
            _logger.info(str(values))
            values = json.loads(values)
            if values.get('topic'):
                if not isinstance(values['topic'], int):
                    topic_search = self.env['kg.topic'].sudo().search([('name', '=', values['topic'])], limit=1)
                    if topic_search:
                        topic = topic_search.id
                    else:
                        new_topic_id = self.env['kg.topic'].sudo().create({'name': values['topic']})
                        topic = new_topic_id.id
            if values.get('customer'):
                if not isinstance(values['customer'], int):
                    customer_search = self.env['res.partner'].sudo().search([('email', '=', values['email'])], limit=1)
                    if customer_search:
                        customer = customer_search
                    else:
                        new_cust_id = self.env['res.partner'].sudo().create(
                            {'name': values['customer'], 'email': values['email'], 'city': values['city']})
                        customer = new_cust_id
            create_ticket_values = {
                'partner_id': customer.id,
                'name': values.get('subject'),
                'form_type': values.get('form_type'),
                'partner_email': customer.email,
                'city_text': customer.city,
                'mob': values.get('mobile'),
                'topic': topic,
                'subject': values.get('subject'),
                'description': values.get('whats_on_mind'),
                'country': uae_id,
            }
            ticket = self.env['helpdesk.ticket'].sudo().create(create_ticket_values)
            if len(ticket) == 1:
                return {"status": '00', "message": "Successfully created Ticket"}
            else:

                return {"status": '01', "message": "Something went wrong!!!!!"}
        except Exception as e:
            _logger.info(str(e))
            if len(ticket) == 1:
                return {"status": '00', "message": "Successfully created Ticket"}
            else:
                return {"status": '01', "message": "Something went wrong : %s" % str(e)}

    def _track_template(self, changes):
        res = super(HelpdeskTicket, self)._track_template(changes)

        if 'stage_id' in changes:
            if self.stage_id.id == self.env.ref('helpdesk.stage_new').id:
                pre_lang = self.partner_id.kg_pre_lang or self.kg_pre_lang or 'english'
                if pre_lang:
                    template = self.env['helpdesk.stage.templates'].search(
                        [('stage_id', '=', self.env.ref('helpdesk.stage_new').id), ('kg_pre_lang', '=', pre_lang)])
                    if template:
                        template = template.template_id

                        res['stage_id'] = (template, {
                            'auto_delete_keep_log': True,
                            'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
                            'email_layout_xmlid': 'mail.mail_notification_light'
                        })

            if self.stage_id.id == self.env.ref('helpdesk.stage_solved').id:
                pre_lang = self.partner_id.kg_pre_lang or self.kg_pre_lang or 'english'
                if pre_lang:
                    template = self.env['helpdesk.stage.templates'].search(
                        [('stage_id', '=', self.env.ref('helpdesk.stage_solved').id), ('kg_pre_lang', '=', pre_lang)])
                    if template:
                        template = template.template_id

                        res['stage_id'] = (template, {
                            'auto_delete_keep_log': True,
                            'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
                            'email_layout_xmlid': 'mail.mail_notification_light'
                        })
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.partner_id:
            if kwargs.get('author_id') == self.partner_id.id:
                if not self.description:
                    self.description = kwargs.get('body')
        if kwargs.get('message_type') == 'comment' and self.stage_id and self.stage_id.id == self.env.ref(
                'helpdesk.stage_new').id:
            self.stage_id = self.env.ref('helpdesk.stage_in_progress').id or None

        kwargs['email_from'] = 'CASIO Care <casiocare@casiomea.com>'

        message = super(HelpdeskTicket, self).message_post(**kwargs)
        return message

    kg_pre_lang = fields.Selection(
        [('english', 'English(الإنجليزية)'), ('arabic', 'Arabic(عربى)'), ('french', 'French(فرنسي)')],
        'Language', compute='_compute_detected_language', default='english', store=True)
    # kg_pre_lang = fields.Selection(
    #     [('english', 'English(الإنجليزية)'), ('arabic', 'Arabic(عربى)'), ('french', 'French(فرنسي)')],
    #     'Language', default='english', store=True)

    topic = fields.Many2one('kg.topic', string='Topic')
    form_type = fields.Selection(
        [('ec_form', 'EC Form'), ('rtn_ec_form', 'Return EC Form'), ('calculator_form', 'Casio Calculator Form')])
    model_id = fields.Many2one('watch.models', string='Model No')
    model_no = fields.Char('Model No')
    city_text = fields.Char('City')
    category_id = fields.Many2one('watch.category', string='Category')
    partner_name = fields.Char(string='Full Name')
    title = fields.Char(string='Title')
    country = fields.Many2one('res.country', string='Country')
    city = fields.Many2one('res.country.state', string='City')
    mob = fields.Char(string='Phone No')
    subject = fields.Char('Subject')
    description_dummy = fields.Text(string='Description')
    product_opened = fields.Selection([('yes', 'Yes'), ('no', 'No')])
    seen = fields.Boolean('Seen', compute='compute_seen')
    edit = fields.Boolean('Last Edit', compute='compute_edit')
    reply_status = fields.Selection(
        [('cme', 'CME REPLIED'), ('customer', 'CUSTOMER REPLIED')],
        'Reply Status', compute='compute_reply_status', store=True)
    occupation = fields.Selection(
        [('student', 'Student'), ('teacher', 'Teacher'), ('other', 'Other')])

    @api.depends('name')
    def _compute_detected_language(self):
        """ Detect and assign the primary language based on the 'name' field."""
        for record in self:
            record.kg_pre_lang = 'english'
            if record.name:
                # try:
                #     main_lang = detect(record.name)
                #     if main_lang == 'ar':
                #         record.kg_pre_lang = 'arabic'
                #     elif main_lang == 'fr':
                #         record.kg_pre_lang = 'french'
                # except:
                #     record.kg_pre_lang = 'english'
                try:
                    detected_langs = detect_langs(record.name)
                    main_lang = str(detected_langs[0]).split(':')[0]

                    if main_lang == 'ar':
                        record.kg_pre_lang = 'arabic'
                    elif main_lang == 'fr':
                        record.kg_pre_lang = 'french'
                except:
                    record.kg_pre_lang = 'english'

    @api.onchange('topic')
    def onchange_topic(self):
        res = {}
        user = self.env.user
        if user.has_group('helpdesk.group_helpdesk_manager'):
            topic = self.env['kg.topic'].search([]).ids
        else:
            topic = self.env['kg.topic'].search([('users_ids', '=', self.env.user.id)]).ids
        res['domain'] = {'topic': [('id', 'in', topic)]}
        return res

    def compute_reply_status(self):
        for record in self:
            if record.id:
                message = self.env['mail.message'].search(
                    [('model', '=', 'helpdesk.ticket'), ('res_id', '=', record.id)], order="date DESC", limit=1)
                if message.author_id and message.author_id.id == record.partner_id.id:
                    record.reply_status = 'customer'
                else:
                    record.reply_status = 'cme'

    def compute_seen(self):
        for record in self:
            if record.id:
                last_seen_record = self.env['auditlog.log'].search(
                    [('model_id.model', '=', 'helpdesk.ticket'), ('user_id', '=', self.env.user.id)],
                    order="res_id DESC", limit=1)
                if last_seen_record:
                    if record.id <= last_seen_record.res_id:
                        record.seen = True
                    else:
                        record.seen = False
                else:
                    record.seen = False

    def compute_edit(self):
        for record in self:
            if record.id:
                last_edit_record = self.env['auditlog.log'].search(
                    [('model_id.model', '=', 'helpdesk.ticket'), ('method', '=', 'write'), ('res_id', '=', record.id)],
                    order="create_date DESC", limit=1)
                if last_edit_record:
                    if self.env.user.id != last_edit_record.user_id.id:
                        record.edit = True
                    else:
                        record.edit = False
                elif record.create_uid.id == 1:
                    record.edit = True
                else:
                    record.edit = False

    def add_marketing_followers(self):
        for record in self:
            for member in record.team_id.marketing_team_ids:
                record.message_subscribe(partner_ids=member.partner_id.ids)

    @api.model
    def create(self, values):
        msg = "Wordpress valuees: " + " ".join(values)
        _logger.debug(msg)
        values['description'] = values.get('description')
        values['description_dummy'] = values.get('description')
        values['stage_id'] = self.env.ref('helpdesk.stage_new') and self.env.ref('helpdesk.stage_new').id or None
        # if not isinstance(values['team_id'],int):
        if not values.get('team_id'):
            values['team_id'] = self.env.ref('helpdesk.helpdesk_team1') and self.env.ref(
                'helpdesk.helpdesk_team1').id or None
        if values.get('topic'):

            if not isinstance(values['topic'], int):
                topic_search = self.env['kg.topic'].search([('name', '=', values['topic'])], limit=1)
                if topic_search:
                    values['topic'] = topic_search.id
                else:
                    new_topic_id = self.env['kg.topic'].create({'name': values['topic']})
                    values['topic'] = new_topic_id.id
        if values.get('category_id'):
            if not isinstance(values['category_id'], int):
                category_search = self.env['watch.category'].search([('name', '=', values['category_id'])], limit=1)
                if category_search:
                    values['category_id'] = category_search.id
                else:
                    new_category_id = self.env['watch.category'].create({'name': values['category_id']})
                    values['category_id'] = new_category_id.id
        if values.get('country'):
            if not isinstance(values['country'], int):
                country_search = self.env['res.country'].search([('name', '=', values['country'])], limit=1)
                if country_search:
                    values['country'] = country_search.id
                else:
                    new_country_id = self.env['res.country'].create({'name': values['country']})
                    values['country'] = new_country_id.id
        res = super(HelpdeskTicket, self).create(values)
        if res.team_id and res.team_id.manager_id:
            res.user_id = res.team_id.manager_id.id
        res.add_marketing_followers()  # Add marketing team as follower
        if res.partner_id:
            res.partner_id.update_agent_order('SVC')
            if not res.partner_id.kg_agent:
                res.partner_id.kg_agent = 'SVC'
            if not res.partner_id.name and res.partner_name:
                res.partner_id.name = res.partner_name
            res.partner_id.from_helpdesk = True
            if res.kg_pre_lang:
                if res.partner_id.new_create_date >= date.today():
                    res.partner_id.kg_pre_lang = res.kg_pre_lang
            if res.mob:
                res.partner_id.mobile = res.mob
            if res.country:
                res.partner_id.country_id = res.country.id
            if res.city_text:
                check_city = self.env['res.country.state'].search([('name', '=', res.city_text)], limit=1)
                if check_city:
                    res.partner_id.kg_area_res = check_city.id
                else:
                    if res.country.id:
                        new_city = self.env['res.country.state'].create(
                            {'name': res.city_text, 'country_id': res.country.id, 'code': res.city_text})
                        res.partner_id.kg_area_res = new_city.id
        return res

    @api.model
    def write(self, vals):
        res = super(HelpdeskTicket, self).write(vals)
        if self.partner_id:
            self.partner_id.update_agent_order('SVC')
            if not self.partner_id.kg_agent:
                self.partner_id.kg_agent = 'SVC'
        return res

    @api.model
    def load_apk(self, vals):
        print(
            '/casio/kg/api/contactus/casio/kg/api/contactus/casio/kg/api/contactus/casio/kg/api/contactus/casio/kg/api/contactus')
        model_obj = self.env['watch.models']
        categ_obj = self.env['watch.category']
        model_id = model_obj.search([('name', '=', vals['model'])], limit=1) or False
        category_id = categ_obj.search([('name', '=', vals['category'])], limit=1) or False
        if not model_id:
            model_id = model_obj.create({'name': vals['model']})
        if not category_id:
            category_id = categ_obj.create({'name': vals['category']})
        self.create({
            'name': vals['name'],
            'model_id': model_id.id,
            'category_id': category_id.id,
            'title': vals['title'],
            'mob': vals['mob'],
            'partner_email': vals['partner_email'],
            'partner_name': vals['partner_name'],
            'country': vals['country'],
            'city': vals['city'],
            'description': vals['description'],

        })
        return "Success"


class HelpdeskTopic(models.Model):
    _name = 'kg.topic'

    name = fields.Char(string='Topic Name')
    users_ids = fields.Many2many('res.users')

# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.modules.module import get_module_resource
import base64


class kg_hobbies(models.Model):
    _name = 'kg.hobbies'

    name = fields.Char('Name')


class kg_casio_brand(models.Model):
    _name = 'kg.casio.brand'

    name = fields.Char('Name')


class kg_age(models.Model):
    _name = 'kg.age'

    name = fields.Char('Name')


class kg_calculator(models.Model):
    _name = 'kg.calculator'

    name = fields.Char('Name')


class Partner(models.Model):
    _inherit = 'res.partner'
    _description = 'Customers'

    @api.model
    def send_birthday_mail(self):
        current_month = datetime.now().month
        current_day = datetime.now().day
        records = self.search([('kg_age_id', '!=', False), ('kg_agent', 'not ilike', 'EDU')]).filtered(
            lambda r: r.kg_age_id.month == current_month).filtered(lambda r: r.kg_age_id.day == current_day)
        for customer in records:
            if customer.kg_pre_lang == 'arabic':
                template = self.env.ref('kg_casio.birthday_arabic_template', False)
                template.send_mail(customer.id, force_send=True)
            else:
                template = self.env.ref('kg_casio.birthday_template', False)
                template.send_mail(customer.id, force_send=True)

    def update_agent_order(self, agent):
        if not self.agent_order:
            vals = {}
            vals['agent_name'] = agent
            vals['order_no'] = 1
            vals['partner_id'] = self.id
            agent_order_id = self.env['agent.order'].create(vals)
            self.agent_order = [(6, 0, [agent_order_id.id])]
        else:
            max_order_no = 0
            find_order = self.env['agent.order'].search([('partner_id', '=', self.id)], order='order_no desc', limit=1)
            if find_order:
                max_order_no = find_order.order_no
            check_if_already = self.env['agent.order'].search(
                [('partner_id', '=', self.id), ('agent_name', '=', agent)])
            if not check_if_already:
                vals = {}
                vals['agent_name'] = agent
                vals['order_no'] = max_order_no + 1
                vals['partner_id'] = self.id
                agent_order_id = self.env['agent.order'].create(vals)
                self.agent_order = [(4, agent_order_id.id)]

    skill_level = fields.Char('Skill Level')
    agent_order = fields.Many2many('agent.order', 'agent_order_partner_rel', 'partner_id', 'order_id', 'Agent Tags')
    from_helpdesk = fields.Boolean('From Helpdesk', default=False)

    kg_phone_code = fields.Char(string="Country Code")
    kg_country_res = fields.Many2one('res.country', string="Nationality(جنسية)")
    kg_area_res = fields.Many2one('res.country.state', string="City(مدينة)", store=True)
    kg_no_vouchers = fields.Integer('Vouchers', compute='_compute_vouchers_count')
    kg_no_purchases = fields.Integer('Purchases', compute='_compute_purchase_count')
    kg_no_tickets = fields.Integer('Tickets', compute='_compute_ticket_count')
    kg_cus_code = fields.Char('Customer ID')
    kg_gender = fields.Selection(
        [('male', 'Male(ذكر)'), ('female', 'Female(أنثى)'), ('no_pref', 'I prefer not to mention(أنا أفضل عدم ذكر)')],
        'Gender')
    kg_first_visit = fields.Selection([('yes', 'Yes(نعم)'), ('no', 'No(لا)')],
                                      'Is this your first visit?(هل هذه زيارتك الأولى؟)')
    kg_fav_brand_ids = fields.Many2many('kg.casio.brand', string="Fav Brands")
    kg_att_casio = fields.Selection([('yes', 'Yes(نعم)'), ('no', 'No(لا)')],
                                    'Would you like to be invited for G-Shock Annual Event?(هل ترغب في تلقي دعوة لأنشطة G-Shock؟)')
    kg_cmnt = fields.Text('Comments(تعليقات)')
    kg_hob_id = fields.Many2many('kg.hobbies', string="Hobbies")
    kg_age_id = fields.Date('Date of Birth')
    kg_heards_abt_casio = fields.Selection([('yes', 'Yes(نعم)'), ('no', 'No(لا)')],
                                           'Have you heard about G-SHOCK brand before?(هل سمعت عن ماركة جي – شوك من قبل ؟ )')
    kg_shop_prefer = fields.Selection([('online', 'Online(عبر الانترنت)'), ('retail', 'Retail(التجزئة)')],
                                      'Which shopping method you prefer?(ما هي طريقتك المفضلة للتسوق :)')
    kg_pre_lang = fields.Selection(
        [('english', 'English(الإنجليزية)'), ('arabic', 'Arabic(عربى)'), ('french', 'French(فرنسي)')],
        'Preferred Language for Communication(اللغة المفضلة للتواصل :)', default='english')

    kg_privacy = fields.Text('User Privacy Agreement, Terms & Conditions (إشعار الخصوصية للمستخدم)')

    kg_agent = fields.Char('Agent')
    kg_cmnt = fields.Text('Comments(تعليقات)')
    kg_join_club = fields.Selection([('gshock', 'G-Shock Club'), ('music', 'Music Club')], 'Join Club Form',
                                    tracking=True)

    # Show create - date only
    new_create_date = fields.Date('Create Date')

    selectable_fields = ['email', 'kg_area_res', 'mobile', 'country_id', 'kg_country_res', 'kg_gender', 'kg_pre_lang',
                         'name', 'kg_first_visit', 'kg_fav_brand_ids', 'kg_att_casio', 'kg_age_id', 'kg_hob_id',
                         'kg_heards_abt_casio', 'kg_agent', 'new_create_date', 'create_uid', 'kg_school_name',
                         'kg_teaching_level',
                         'kg_teaching_subject', 'kg_using_calculator', 'kg_list_calculator', 'agent_order']

    kg_school_name = fields.Char(string="School Name")
    kg_teaching_level = fields.Char(string="Teaching Level")
    kg_teaching_subject = fields.Char(string="Teaching Subject")
    kg_using_calculator = fields.Char(string="Using Calculator")
    kg_list_calculator = fields.Char(string="Listed Calculator")

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(Partner, self).fields_get(allfields, attributes=attributes)
        not_selectable_fields = set(self._fields.keys()) - set(self.selectable_fields)
        for field in not_selectable_fields:
            if field in res:
                res[field]['selectable'] = False
        return res

    def _compute_vouchers_count(self):
        Voucher = self.env['kg.voucher']
        for partner in self:
            partner.kg_no_vouchers = Voucher.search_count([('kg_customer_id', '=', partner.id)])

    def _compute_purchase_count(self):
        Invoice = self.env['kg.cust.inv']
        for partner in self:
            partner.kg_no_purchases = Invoice.search_count([('kg_cas_customer_id', '=', partner.id)])

    def _compute_ticket_count(self):

        res = super(Partner, self)._compute_ticket_count()
        for rec in self:
            rec.kg_no_tickets = rec.ticket_count
        # Ticket = self.env['helpdesk.ticket']
        # self.kg_no_tickets = False
        # for partner in self:
        # 	partner.kg_no_tickets = Ticket.search_count([('partner_id', '=', partner.id),'|',('active','=',True),('active','=',False)])
        return res

    @api.depends('create_date')
    def _compute_create_date(self):
        for record in self:
            record.new_create_date = datetime.strftime(record.create_date, "%Y-%m-%d")

    @api.model
    def create(self, vals):
        sequence_code = 'kg.cus'
        vals['kg_cus_code'] = self.env['ir.sequence'].next_by_code(sequence_code) or '/'
        country_obj = self.env['res.country'].browse(vals.get('country_id'))
        vals['kg_phone_code'] = 'Mobile+(رقم هاتف الجوال :)' + '(' + str(country_obj.phone_code) + ')'
        duplicate_check = self.env['kg.voucher']
        res = super(Partner, self).create(vals)
        if vals.get('kg_agent'):
            res.update_agent_order(vals['kg_agent'])
        fav_brand = []
        for brand in res.kg_fav_brand_ids:
            fav_brand.append(brand.name)
        fav_brand_name = ','.join(map(str, fav_brand))

        hobb_list = []
        for hob in res.kg_hob_id:
            hobb_list.append(hob.name)
        hobb_name = ','.join(map(str, hobb_list))

        if 'new_create_date' not in vals:
            res.write({"new_create_date": res.create_date})

        return res

    @api.model
    def create_cus(self, vals_mob):
        def check_input(a):
            if type(a) is int:
                return a
            if type(a) is str:
                if a.isdigit():
                    return int(a)
                else:
                    return 0

        vals = {}
        if vals_mob.get('heardAboutGShock'):
            vals['kg_heards_abt_casio'] = vals_mob.get('heardAboutGShock').lower()

        if vals_mob.get('shoppingMethod'):
            vals['kg_shop_prefer'] = vals_mob.get('shoppingMethod').lower()

        if vals_mob.get('annualEventInterest'):
            vals['kg_att_casio'] = vals_mob.get('annualEventInterest').lower()

        vals['name'] = vals_mob.get('fullName')

        if vals_mob.get('countryOfResidence'):
            country_no = check_input(vals_mob.get('countryOfResidence'))
            country_id = self.env['res.country'].search([('id', '=', country_no)])
            if country_id:
                vals['country_id'] = country_id.id

        if vals_mob.get('nationality'):
            nationality_no = check_input(vals_mob.get('nationality'))
            country_id = self.env['res.country'].search([('id', '=', nationality_no)])
            if country_id:
                vals['kg_country_res'] = country_id.id
        vals['email'] = vals_mob.get('email')

        vals['kg_agent'] = vals_mob.get('agent')
        vals['mobile'] = vals_mob.get('mobileNumber')
        vals['kg_gender'] = vals_mob.get('gender').lower()
        dob = datetime.strptime(vals_mob.get('ageGroup'), "%d/%m/%Y").strftime("%Y-%m-%d")
        vals['kg_age_id'] = dob
        # if vals_mob.get('ageGroup'):
        #     age_id = self.env['kg.age'].search([('name', '=', vals_mob.get('ageGroup'))])
        #     if age_id:
        #         vals['kg_age_id'] = age_id.id

        if vals_mob.get('areaOfResidence'):
            area_no = check_input(vals_mob.get('areaOfResidence'))
            area_id = self.env['res.country.state'].search([('id', '=', area_no)])
            if area_id:
                vals['kg_area_res'] = area_id.id
        # else:
        #     code = (vals_mob.get('areaofResidence'))[:2]
        #     vals['kg_area_res'] = self.env['res.country.state'].create(
        #         {'code': code, 'name': vals_mob.get('areaOfResidence')}).id
        vals['kg_pre_lang'] = vals_mob.get('preferredLanguage').lower()
        vals['kg_cmnt'] = vals_mob.get('comments')
        cus_id = self.create(vals)
        if cus_id.kg_pre_lang == 'arabic':
            template = self.env.ref('kg_casio.welcome_mail_arabic_template', False)
            template.send_mail(cus_id.id, force_send=True)
        elif cus_id.kg_pre_lang == 'french':
            template = self.env.ref('kg_casio.welcome_mail_template_french', False)
            template.send_mail(cus_id.id, force_send=True)
        else:
            template = self.env.ref('kg_casio.welcome_mail_template', False)
            template.send_mail(cus_id.id, force_send=True)

        if cus_id:
            if vals_mob.get('favoriteBrand') != '':
                cus_id.write({'kg_fav_brand_char': vals_mob.get('favoriteBrand')})
                favbrand = vals_mob.get('favoriteBrand').split(",")
                h_ids = []
                if favbrand:
                    for i in favbrand:
                        h = self.env['kg.casio.brand'].search([('name', '=', i)])
                        if h:
                            self._cr.execute(
                                'INSERT INTO kg_casio_brand_res_partner_rel (res_partner_id, kg_casio_brand_id) values (%s, %s)',
                                (cus_id.id, h.id))

            if vals_mob.get('hobbies') != '':
                cus_id.write({'kg_hob_char': vals_mob.get('hobbies')})
                hobby = vals_mob.get('hobbies').split(",")
                h_ids = []
                if hobby:
                    for i in hobby:
                        h = self.env['kg.hobbies'].search([('name', '=', i)])
                        if h:
                            self._cr.execute(
                                'INSERT INTO kg_hobbies_res_partner_rel (res_partner_id, kg_hobbies_id) values (%s, %s)',
                                (cus_id.id, h.id))
                        #  vals['kg_hob_id']= [[ 6, 0, h_ids ]]
            vou_id = self.env['kg.voucher'].search([('kg_customer_id', '=', cus_id.id)])
            if vou_id:
                return 'Voucher No is ' + (vou_id.name or '')
            else:
                return "Customer created successfully."
        else:
            return 'Voucher Not Created'

# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from odoo import api, fields, models, _
# from odoo.exceptions import Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class kg_cust_inv(models.Model):
    _name = 'kg.cust.inv'

    selectable_fields = ['create_date', 'kg_pur_date', 'kg_salesperson', 'kg_voucher_id', 'kg_price_after_disc',
                         'kg_price_bef_disc', 'name']

    kg_cas_customer_id = fields.Many2one("res.partner", string="Customer")
    


    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(kg_cust_inv, self).fields_get(allfields, attributes=attributes)
        not_selectable_fields = set(self._fields.keys()) - set(self.selectable_fields)
        for field in not_selectable_fields:
            if field in res:
                res[field]['selectable'] = False

        return res

    name = fields.Char('Name')
    kg_pur_date = fields.Date('Date of Purchase')
    kg_salesperson = fields.Char('Salesperson')
    kg_voucher_id = fields.Many2one('kg.voucher', 'Voucher')
    kg_outlet_id = fields.Char('Outlet')
    kg_price_after_disc = fields.Float('Price After Discount')
    kg_price_bef_disc = fields.Float('Price Before Discount')
    kg_inv_disc = fields.Float('Invoice Discount', compute='_compute_price')
    kg_inv_lines = fields.One2many('kg.inv.lines', 'kg_cust_inv_id', 'Lines')
    email_cus = fields.Char('Email', related='kg_cas_customer_id.email', store=True)
    mobile_cus = fields.Char('Mobile', related='kg_cas_customer_id.mobile', store=True)


    @api.model
    def create(self, vals):
        ## Adding Customer Code
        sequence_code = 'kg.cus.inv'
        # Commented for import
        vals['name'] = self.env['ir.sequence'].next_by_code(sequence_code) or '/'
        res = super(kg_cust_inv, self).create(vals)
        return res

    def _compute_price(self):
        for record in self:
            record.kg_inv_disc = record.kg_price_bef_disc - record.kg_price_after_disc

    @api.model
    def check_cust(self,vals):
        mobile_no = vals.get('mobile')
        email = vals.get('email')
        customer = self.env['res.partner'].search([('mobile','=',mobile_no),('email','=',email)],limit=1) or self.env['res.partner'].search([('mobile','=',mobile_no)],limit=1) or self.env['res.partner'].search([('email','=',email)],limit=1)
        output = {}
        if customer:

            output['customer_id'] = customer.id
            output['status'] = 'Success'
            return output
        else:
            output['status']='Failed'
            return output

    @api.model
    def create_inv(self, vals):
        new = {}
        customer_id = vals['CustomerID']
        if customer_id:
            if customer_id.isdigit():
                customer_obj = self.env['res.partner'].search([('id','=',int(customer_id))])
            else:
                return False
        output={}
        if not customer_obj:
            return False
        else:
            new['kg_cas_customer_id'] = customer_obj.id
            new['kg_outlet_id'] = vals['OutletID']
            new['kg_salesperson'] = vals['SalesPersonID']
            new['kg_pur_date'] = datetime.strptime(vals['DateOfPurchase'], '%d-%m-%Y').date()
            new['kg_price_after_disc'] = float(vals['PriceAfterDiscount'])
            new['kg_price_bef_disc'] = float(vals['PriceBeforeDiscount'])
            new_id = self.create(new)
            for line in vals['items']:
                new_line = {}
                new_line['name'] = line['SKUNumber']
                new_line['kg_price_bef_disc'] = float(line['PriceBeforeDiscount'])
                new_line['kg_price_after_disc'] = float(line['PriceAfterDiscount'])
                new_line['kg_cust_inv_id'] = new_id.id
                self.env['kg.inv.lines'].create(new_line)
            output['status']='Success'
            output['inv_no'] = new_id.name
            return output


class kg_inv_lines(models.Model):
    _name = 'kg.inv.lines'
    name = fields.Char('SKU No')
    kg_price_after_disc = fields.Float('Price After Discount')
    kg_price_bef_disc = fields.Float('Price Before Discount')
    kg_cust_inv_id = fields.Many2one('kg.cust.inv', 'Customer Inv ID')
    date_of_purchase = fields.Date('Date of Purchase',related='kg_cust_inv_id.kg_pur_date',store=True)
    outlet = fields.Char('Outlet',related='kg_cust_inv_id.kg_outlet_id',store=True)
    salesperson = fields.Char('Salesperson',related='kg_cust_inv_id.kg_salesperson',store=True)
    customer_id = fields.Many2one('res.partner',related='kg_cust_inv_id.kg_cas_customer_id',store=True,string='Customer')
    email_cus = fields.Char('Email',related='customer_id.email',store=True)
    mobile_cus = fields.Char('Mobile',related='customer_id.mobile',store=True)
    agent_cus = fields.Char('Agent',related='customer_id.kg_agent',store=True)
    city_cus = fields.Many2one('res.country.state',related='customer_id.kg_area_res',store=True,string='City')
    nationality_cus = fields.Many2one('res.country',related='customer_id.kg_country_res',store=True,string='Nationality')
    country_cus = fields.Many2one('res.country',related='customer_id.country_id',store=True,string='Country')
    age_cus = fields.Date('Date of Birth',related='customer_id.kg_age_id',store=True)
    gender_cus  = fields.Selection(
		[('male', 'Male(ذكر)'), ('female', 'Female(أنثى)'), ('no_pref', 'I prefer not to mention(أنا أفضل عدم ذكر)')],
		string='Gender',related='customer_id.kg_gender',store=True)

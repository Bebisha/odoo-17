# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    pdc_customer = fields.Many2one(
        'account.account', string="PDC Account for customer")

    pdc_vendor = fields.Many2one(
        'account.account', string="PDC Account for Vendor")

    cdc_customer = fields.Many2one(
        'account.account', string="CDC Account for customer")

    cdc_vendor = fields.Many2one(
        'account.account', string="CDC Account for Vendor")
    cheque_send_to_ids = fields.Many2many('res.users','cheque_send_to_ids_rel', string="Cheque Send to")
    cheque_notification_send = fields.Float(string='Cheque notification send before')


    #=============
    # Customer
    #=============
    
    is_cust_due_notify = fields.Boolean('Customer Due Notification')
    
    is_notify_to_customer = fields.Boolean('Notify to Customer')
    
    is_notify_to_user = fields.Boolean('Notify to Internal User ')
    
    sh_user_ids = fields.Many2many('res.users',relation='sh_user_ids_customer_company_rel',string='Responsible User')
    
    notify_on_1 = fields.Char(string='Notify On 1')
    
    notify_on_2 = fields.Char(string='Notify On 2')
    
    notify_on_3 = fields.Char(string='Notify On 3')
    
    notify_on_4 = fields.Char(string='Notify On 4')
    
    notify_on_5 = fields.Char(string='Notify On 5')
    
    #=============
    # Vendor
    #=============

    is_vendor_due_notify = fields.Boolean('Vendor Due Notification')
    
    is_notify_to_vendor = fields.Boolean('Notify to Vendor')
    
    is_notify_to_user_vendor = fields.Boolean('Notify to internal User')
     
    sh_user_ids_vendor = fields.Many2many('res.users',relation='sh_user_ids_vendor_company_rel',string='Responsible User ')
    
    notify_on_1_vendor = fields.Char(string='Notify on 1')
    
    notify_on_2_vendor = fields.Char(string='Notify on 2')
    
    notify_on_3_vendor = fields.Char(string='Notify on 3')
    
    notify_on_4_vendor = fields.Char(string='Notify on 4')
    
    notify_on_5_vendor = fields.Char(string='Notify on 5')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pdc_customer = fields.Many2one('account.account', string="PDC Account for customer",
                                   related='company_id.pdc_customer', readonly=False)

    pdc_vendor = fields.Many2one('account.account', string="PDC Account for Vendor",
                                 related='company_id.pdc_vendor', readonly=False)

    cdc_customer = fields.Many2one('account.account', string="CDC Account for customer",
                                   related='company_id.cdc_customer', readonly=False)

    cdc_vendor = fields.Many2one('account.account', string="CDC Account for Vendor",
                                 related='company_id.cdc_vendor', readonly=False)
    
    #=============
    # Customer
    #=============
    
    is_cust_due_notify = fields.Boolean('Customer Due Notification',
                                        related='company_id.is_cust_due_notify',readonly=False)
    
    is_notify_to_customer = fields.Boolean('Notify to Customer',
                                        related='company_id.is_notify_to_customer',readonly=False)
    
    is_notify_to_user = fields.Boolean('Notify to Internal User',
                                        related='company_id.is_notify_to_user',readonly=False)
    
    sh_user_ids = fields.Many2many('res.users',string='Responsible User',
                                        related='company_id.sh_user_ids',readonly=False)
    
    notify_on_1 = fields.Char('Notify On 1',
                              related='company_id.notify_on_1',readonly=False)
    
    notify_on_2 = fields.Char('Notify On 2',
                              related='company_id.notify_on_2',readonly=False)
    
    notify_on_3 = fields.Char('Notify On 3',
                              related='company_id.notify_on_3',readonly=False)
    
    notify_on_4 = fields.Char('Notify On 4',
                              related='company_id.notify_on_4',readonly=False)
    
    notify_on_5 = fields.Char('Notify On 5',
                              related='company_id.notify_on_5',readonly=False)
    
    #=============
    # Vendor
    #=============
    is_vendor_due_notify = fields.Boolean('Vendor Due Notification',
                                        related='company_id.is_vendor_due_notify',readonly=False)
    
    is_notify_to_vendor = fields.Boolean('Notify to Vendor',
                                        related='company_id.is_notify_to_vendor',readonly=False)
    
    is_notify_to_user_vendor = fields.Boolean('Notify to Internal User ',
                                              related='company_id.is_notify_to_user_vendor',readonly=False)
    
    sh_user_ids_vendor = fields.Many2many('res.users',string='Responsible User ',
                                        related='company_id.sh_user_ids_vendor',readonly=False)
    
    notify_on_1_vendor = fields.Char('Notify on 1',
                              related='company_id.notify_on_1_vendor',readonly=False)
    
    notify_on_2_vendor = fields.Char('Notify on 2',
                              related='company_id.notify_on_2_vendor',readonly=False)
    
    notify_on_3_vendor = fields.Char('Notify on 3',
                              related='company_id.notify_on_3_vendor',readonly=False)
    
    notify_on_4_vendor = fields.Char('Notify on 4',
                              related='company_id.notify_on_4_vendor',readonly=False)
    
    notify_on_5_vendor = fields.Char('Notify on 5',
                              related='company_id.notify_on_5_vendor',readonly=False)

    cheque_send_to_ids = fields.Many2many('res.users',related='company_id.cheque_send_to_ids',readonly=False, string="Cheque Send to")

    cheque_notification_send = fields.Float(string='Cheque notification send before',related='company_id.cheque_notification_send',readonly=False)


    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     try:
    #         cheque_send_to_ids = self.env['ir.config_parameter'].sudo().get_param('many2many.cheque_send_to_ids')
    #         cheque_notification_send = float(self.env['ir.config_parameter'].sudo().get_param('many2many.cheque_notification_send'))
    #         res.update({
    #             'cheque_send_to_ids': [
    #                 (6, 0, [int(x) for x in cheque_send_to_ids.split(',')])] if cheque_send_to_ids else False,
    #             'cheque_notification_send': cheque_notification_send,
    #         })
    #     except Exception as e:
    #         _logger.exception(e)
    #     return res
    #
    # def set_values(self):
    #     res = super(ResConfigSettings, self).set_values()
    #     try:
    #         self.env['ir.config_parameter'].sudo().set_param('many2many.cheque_send_to_ids',
    #                                                          ','.join(map(str, self.cheque_send_to_ids.ids)))
    #         self.env['ir.config_parameter'].sudo().set_param('many2many.cheque_notification_send',
    #                                                          str(self.cheque_notification_send))
    #     except Exception as e:
    #         _logger.exception(e)
    #     return res
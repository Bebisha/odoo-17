from odoo import models,fields,api


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    lead_activities = fields.Selection([('call', 'Call'),
                                        ('email', 'Email'),
                                        ('followups', 'Followups'),
                                        ('new_leads', 'New Leads'),
                                        ('meetings', 'Meetings'),
                                        ('demos', 'Demos'),
                                        ('proposals', 'Proposals'),
                                        ('negotiation', 'Negotiation'),
                                        ('order_confirmation', 'Order Confirmation'),
                                        ('kick_off', 'Kick-Off'),
                                        ('cold_calls', 'No.of Contacts Identified for Cold Calls'),
                                        ])


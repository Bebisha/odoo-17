from odoo import models, fields,api


class AccountMove(models.Model):
    _inherit = 'account.move'

    inv_attachment_ids = fields.Many2many("invoice.attachment.master",string="Attachment" )
    company_partner_id = fields.Many2one('res.partner', related='company_id.partner_id', string='Account Holder', readonly=True, store=True)

    bank_id = fields.Many2many(
        'res.partner.bank',
    #     string="Bank Account",domain="[('partner_id','=',company_partner_id)]"
    )




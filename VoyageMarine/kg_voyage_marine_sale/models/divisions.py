from odoo import models, fields, api, _


class KGDivisions(models.Model):
    _name = "kg.divisions"
    _description = "Divisions"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    division = fields.Char(string="Division", required=True)
    qtn_sequence_id = fields.Many2one("ir.sequence", string="Quotation Sequence")
    so_sequence_id = fields.Many2one("ir.sequence", string="SO Sequence")

    @api.model_create_multi
    def create(self, vals):
        division = super(KGDivisions, self).create(vals)
        for rec in division:
            if rec.division:
                if not rec.qtn_sequence_id:
                    rec.qtn_sequence_id = self.env['ir.sequence'].sudo().create({
                        'name': rec.name + ' ' + _('Quotation Sequence') + ' ' + rec.division,
                        'padding': 4,
                        'company_id': False,
                        'use_date_range': True,
                        'implementation': 'no_gap',
                    }).id
                if not rec.so_sequence_id:
                    rec.so_sequence_id = self.env['ir.sequence'].sudo().create({
                        'name': rec.name + ' ' + _('Sales Order Sequence') + ' ' + rec.division,
                        'padding': 4,
                        'company_id': False,
                        'use_date_range': True,
                        'implementation': 'no_gap',
                    }).id
        return division


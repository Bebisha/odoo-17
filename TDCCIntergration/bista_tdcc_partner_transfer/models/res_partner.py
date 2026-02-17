# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sibling_ids = fields.Many2many('res.partner', 'student_sibling_rel',
                                   'partner_id', 'sibling_id',
                                   string="Siblings")
    hide_peppol_fields = fields.Char()
    is_coa_installed = fields.Char()

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if vals.get('sibling_ids') and not self.env.context.get(
                'from_sibling_create'):
            for sibling_id in res.sibling_ids:
                sibling_id.with_context(
                    from_sibling_create=True).sibling_ids += res
        return res

    # @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if vals.get('sibling_ids') and not self.env.context.get(
                'from_sibling_write'):
            for partner in self:
                sibling_ids = partner.sibling_ids
                for sibling_id in partner.sibling_ids:
                    sibling_id.with_context(
                        from_sibling_write=True).sibling_ids += partner + (
                            sibling_ids - sibling_id)
        return res

# -*- coding: utf-8 -*-
from odoo import fields, models, api


class HRContract(models.Model):
    _inherit = 'hr.contract'

    total_sal = fields.Float(string='Total Salary',  compute='_get_total_sal')

    @api.depends('wage', 'l10n_ae_housing_allowance', 'l10n_ae_other_allowances', 'l10n_ae_transportation_allowance')
    def _get_total_sal(self):
        """ To store total salary of employee """
        for contract in self:
            total = contract.wage + contract.l10n_ae_housing_allowance + contract.l10n_ae_other_allowances + contract.l10n_ae_transportation_allowance
            contract.total_sal = total

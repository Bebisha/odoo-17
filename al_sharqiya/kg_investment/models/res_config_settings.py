from odoo import api, fields, models, _
from ast import literal_eval
from odoo.addons.base.models.res_partner import _tz_get



class KGInvestmentResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stock_input_account = fields.Many2one('account.account', string='Stock Input Account')
    stock_output_account = fields.Many2one('account.account', string='Stock Output Account')
    stock_valuation_account = fields.Many2one('account.account', string='Stock Valuation Account')
    stock_account_journal = fields.Many2one('account.journal', string='Stock Account Journal')
    market_fvtpl_account_id = fields.Many2one('account.account', string='FVTPL Account')
    market_fvoci_account_id = fields.Many2one('account.account', string='FVOCI Account')
    dividend_account_id = fields.Many2one('account.account', string='Dividend Account')
    revaluation_account_id = fields.Many2one('account.account', string='Revaluation Reserve Account')
    bond_account_id = fields.Many2one('account.account', string='Bonds Account')


    def set_values(self):
        res = super(KGInvestmentResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("kg_investment.stock_input_account",
                                                         self.stock_input_account.id)
        self.env['ir.config_parameter'].sudo().set_param("kg_investment.stock_output_account",
                                                         self.stock_output_account.id)
        self.env['ir.config_parameter'].sudo().set_param("kg_investment.stock_valuation_account",
                                                         self.stock_valuation_account.id)
        self.env['ir.config_parameter'].sudo().set_param("kg_investment.stock_account_journal",
                                                         self.stock_account_journal.id)
        self.env['ir.config_parameter'].sudo().set_param("kg_investment.market_fvtpl_account_id",
                                                         self.market_fvtpl_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param("kg_investment.market_fvoci_account_id",
                                                         self.market_fvoci_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param("kg_investment.dividend_account_id",
                                                         self.dividend_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param("kg_investment.revaluation_account_id",
                                                         self.revaluation_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param("kg_investment.bond_account_id",
                                                         self.bond_account_id.id)

        return res

    @api.model
    def get_values(self):
        res = super(KGInvestmentResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        input_account = params.get_param('kg_investment.stock_input_account', default=False)
        output_account = params.get_param('kg_investment.stock_output_account', default=False)
        valuation_account = params.get_param('kg_investment.stock_valuation_account', default=False)
        account_journal = params.get_param('kg_investment.stock_account_journal', default=False)
        market_fvoci_account_id = params.get_param('kg_investment.market_fvoci_account_id', default=False)
        market_fvtpl_account_id = params.get_param('kg_investment.market_fvtpl_account_id', default=False)
        dividend_account_id = params.get_param('kg_investment.dividend_account_id', default=False)
        revaluation_account_id = params.get_param('kg_investment.revaluation_account_id', default=False)
        bond_account_id = params.get_param('kg_investment.bond_account_id', default=False)

        res.update(
            stock_input_account=int(input_account) if input_account else False,
            stock_output_account=int(output_account) if output_account else False,
            stock_valuation_account=int(valuation_account) if valuation_account else False,
            stock_account_journal=int(account_journal) if account_journal else False,
            dividend_account_id=int(dividend_account_id) if dividend_account_id else False,
            market_fvtpl_account_id=int(market_fvtpl_account_id) if market_fvtpl_account_id else False,
            market_fvoci_account_id=int(market_fvoci_account_id) if market_fvoci_account_id else False,
            bond_account_id=int(bond_account_id) if bond_account_id else False,
            revaluation_account_id=int(revaluation_account_id) if revaluation_account_id else False,)
        return res



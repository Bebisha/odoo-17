# -*- coding: utf-8 -*-
from odoo import models, api,fields,_

class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_order_id = fields.Many2one('kg.purchase.order', string='Purchase Order')
    market_rate_id = fields.Many2one('market.rate.updation')
    kg_sale_id = fields.Many2one('kg.sale.order')
    dividend_id = fields.Many2one('kg.dividend.entry')
    bond_id = fields.Many2one('kg.bonds')
    revaluation_id = fields.Many2one('kg.revaluation.journal')

class AccountAccount(models.Model):
    _inherit = 'account.account'

    account_type = fields.Selection(
        selection_add=[
            ("asset_property_equipment", "Property and equipment"),
            ("asset_lease_receivables", "Lease Receivables"),
            ("asset_investment_subsidiary", "Investment in subsidiary"),
            ("asset_financial_asset_fvoci", "Financial assets at FVOCI"),
            ("asset_financial_asset_fvtpl", "Financial assets at FVTPL"),
            ("asset_perpetual_bonds", "Investments in Perpetual Bonds"),
            ("asset_deferred_taxes", "Deferred Tax Assets"),
            ("asset_amortised_cost_bonds", "Amortised cost of Bonds"),
            ("asset_term_deposit", "Term Deposit "),
            ("equity_share_capital", "Share Capital"),
            ("equity_legal_reserve", "Legal Reserve"),
            ("equity_fair_value_reserve", "Fair Value Reserve"),
            ("equity_retained_earnings", "Retained Earnings"),
            ("liability_end_of_service_benefits", "End of Service Benefits"),
            ("liability_due_to_subsidiary", "Due to Subsidiary"),
            ("liability_accruals", "Accruals and Other Payables"),
            ("liability_taxation", "Provision for Taxation"),
            ("liability_lease_payable_current", "Finance lease payable"),
            ("liability_lease_payable_non", "Finance lease payable"),
            ("income_receivable", "Finance Lease Receivable"),
            ("income_dividend", "Dividend Income"),
            ("income_dividend_subsidiary", "Dividend from Subsidiary"),
            ("income_maintenance", "Maintenance Service Income"),
            ("income_FVTPL", "Unrealised Gain on assets at FVTPL"),
            ("income_RFVTPL", "Realised gain on disposal of asset at FVTPL"),
            ("income_management", "Management Charges Income"),
            ("income_interest_bonds", "Interest Income from Bonds"),
            ("expense_interest", "Interest and Finance Expenses"),
            ("expense_staff_cost", "Staff Cost"),
            ("expense_lease_payable", "Finance Cost on Lease Payable"),
            ("expense_depreciation", "Depreciation"),
            ("expense_administrative", "General Administrative Expenses"),
        ],
        ondelete={'asset_property_equipment': 'cascade', 'asset_lease_receivables': 'cascade', 'asset_investment_subsidiary': 'cascade',
                  'asset_financial_asset_fvoci': 'cascade','asset_financial_asset_fvtpl':'cascade','asset_perpetual_bonds': 'cascade','asset_deferred_taxes': 'cascade','asset_amortised_cost_bonds': 'cascade',
                  'asset_term_deposit': 'cascade','equity_share_capital': 'cascade','equity_legal_reserve': 'cascade','equity_fair_value_reserve': 'cascade','equity_retained_earnings': 'cascade',
                  'liability_end_of_service_benefits': 'cascade','liability_due_to_subsidiary': 'cascade','liability_accruals': 'cascade','liability_taxation': 'cascade','liability_lease_payable_non':'cascade','liability_lease_payable_current':'cascade',
                  'income_receivable': 'cascade','income_dividend': 'cascade','income_maintenance': 'cascade','income_FVTPL': 'cascade','income_dividend_subsidiary': 'cascade','income_management': 'cascade','income_interest_bonds': 'cascade','income_RFVTPL':'cascade',
                  'expense_interest': 'cascade','expense_staff_cost': 'cascade','expense_lease_payable': 'cascade','expense_depreciation': 'cascade','expense_administrative': 'cascade',
                  })

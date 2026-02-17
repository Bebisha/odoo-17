from odoo import fields, models, _


class AssetsReportCustomHandler(models.AbstractModel):
    _inherit = 'account.asset.report.handler'

    def _simulate_imported_depreciation(self, options, results):
        date_from = fields.Date.to_date(options['date']['date_from'])
        date_to = fields.Date.to_date(options['date']['date_to'])
        for al in results:
            if al['asset_already_depreciated_amount_import']:
                asset_values = {
                    'acquisition_date': al['asset_acquisition_date'],
                    'original_value': al['asset_original_value'],
                    'salvage_value': al['asset_salvage_value'],
                    'account_depreciation_id': al['account_id'],
                    'method': al['asset_method'],
                    'method_number': al['asset_method_number'],
                    'method_period': al['asset_method_period'],
                    'method_progress_factor': al['asset_method_progress_factor'],
                    'prorata_computation_type': al['asset_prorata_computation_type'],
                    'prorata_date': al['asset_prorata_date'],
                }
                dummy = self.env['account.asset'].new(asset_values)
                dummy_already_depreciated = self.env['account.asset'].new({
                    'already_depreciated_amount_import': al['asset_already_depreciated_amount_import'],
                    'original_value': -al['asset_original_value'],
                    **asset_values,
                })
                amount_before = al['asset_already_depreciated_amount_import']
                amount_during = 0
                asset_date = al['asset_date']
                for sign, dummy_board in [
                    (1, dummy._recompute_board()),
                    (-1, dummy_already_depreciated._recompute_board()),
                ]:
                    for move_vals in dummy_board:
                        asset_date = min([asset_date, move_vals['date']])
                        line_vals = next(
                            line[2]
                            for line in move_vals['line_ids']
                            if line[2]['account_id'] == al['account_id']
                        )
                        balance = line_vals['debit'] - line_vals['credit']
                        if move_vals['date'] < date_from:
                            amount_before += sign * balance
                        if date_from <= move_vals['date'] <= date_to:
                            amount_during += sign * balance
                al['depreciated_before'] -= amount_before
                al['depreciated_during'] -= amount_during
                al['asset_date'] = asset_date

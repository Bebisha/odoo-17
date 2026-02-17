from odoo import models

class CorporateTaxFloorHandler(models.AbstractModel):
    _name = "ae.ct.floor.tax.handler"
    _inherit = "account.report.custom.handler"
    _description = "Corporate Tax Floor Handler"

    def _report_custom_engine_custom_line_postprocess(
        self, expressions, options, date_scope, current_groupby, next_groupby, offset=0, limit=None, warnings=None
    ):
        """
        Compute Corporate Tax Amount, floored at zero.
        """

        report = self.env['account.report'].browse(options['report_id'])

        # Helper: get value from a line code
        def get_line_value(code):
            line = next((l for l in report.line_ids if l.code == code), None)
            if not line or not line.expression_ids:
                return 0.0
            # If it's a constant formula like 375000 or 9, convert it
            try:
                return float(line.expression_ids[0].formula)
            except Exception:
                # fallback if formula is not directly numeric
                return 0.0

        taxable = get_line_value("AE_CORP_TAXABLE")
        perc = get_line_value("AE_CORP_TAX_PERC")

        # Compute tax and floor at 0
        value = taxable * (perc / 100)
        if value < 0:
            value = 0.0

        # Company currency
        currency = self.env.company.currency_id

        result = {
            'columns': [{
                'no_format': value,
                'name': report.format_value(options, value, figure_type="monetary"),
                'currency_id': currency.id if currency else None,
            }],
            'code': 'AE_CORP_PAYABLE',
            'level': 0,
        }

        if current_groupby:
            return [(None, result)]
        return result

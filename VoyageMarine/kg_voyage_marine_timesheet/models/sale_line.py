from odoo import models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):
        vals = super()._timesheet_create_project_prepare_values()

        vals['description'] = self.name

        return vals
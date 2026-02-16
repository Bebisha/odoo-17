from odoo import models, fields,api

class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    stock_recipient_id = fields.Many2many('res.partner', string="Stock Recipients",column1='stock')

    # stock_report_recipient_ids= fields.Many2many(
    #     'res.partner',
    #     string='Stock Report Recipients',
    #     help='Recipients who will receive the weekly Stock report email.'
    # )


    @api.model
    def get_values(self):
        res = super(ConfigSettings, self).get_values()
        # Retrieve the parameter value, default to an empty string if not set
        sales_report_recipients_param = self.env['ir.config_parameter'].sudo().get_param('kg_stock_move_report.stock_recipient_id', default='')
        # Split the parameter value into IDs, filtering out empty values
        sales_report_recipients_ids = [int(id) for id in sales_report_recipients_param.split(',') if id.isdigit()]
        # Update the res dictionary with the Many2many field value
        res.update({
            'stock_recipient_id': [(6, 0, sales_report_recipients_ids)]
        })
        return res
    #
    def set_values(self):
        super(ConfigSettings, self).set_values()
        # Convert the Many2many recordset to a list of IDs
        sales_report_recipients_ids = [str(partner.id) for partner in self.stock_recipient_id]
        # Store the IDs as a comma-separated string
        self.env['ir.config_parameter'].sudo().set_param(
            'kg_stock_move_report.stock_recipient_id',
            ','.join(sales_report_recipients_ids)
        )
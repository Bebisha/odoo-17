from odoo import models, fields,api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sales_report_recipients = fields.Many2many(
        'res.partner',
        string='Sales Report Recipients',
        help='Recipients who will receive the weekly sales report email.'
    )


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        # Retrieve the parameter value, default to an empty string if not set
        sales_report_recipients_param = self.env['ir.config_parameter'].sudo().get_param('saleperson_weekly_report.sales_report_recipients', default='')
        # Split the parameter value into IDs, filtering out empty values
        sales_report_recipients_ids = [int(id) for id in sales_report_recipients_param.split(',') if id.isdigit()]
        # Update the res dictionary with the Many2many field value
        res.update({
            'sales_report_recipients': [(6, 0, sales_report_recipients_ids)]
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        # Convert the Many2many recordset to a list of IDs
        sales_report_recipients_ids = [str(partner.id) for partner in self.sales_report_recipients]
        # Store the IDs as a comma-separated string
        self.env['ir.config_parameter'].sudo().set_param(
            'saleperson_weekly_report.sales_report_recipients',
            ','.join(sales_report_recipients_ids)
        )
    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     self.env['ir.config_parameter'].sudo().set_param(
    #         'sales_report_recipients',
    #         self.sales_report_recipients.ids
    #     )

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     res.update(
    #         sales_report_recipients=self.env['ir.config_parameter'].sudo().get_param(
    #             'sales_report_recipients', default=[]))
    #     return res

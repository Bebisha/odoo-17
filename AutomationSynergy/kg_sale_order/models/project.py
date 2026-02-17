from odoo import models, api, fields


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sale_order_ids = fields.One2many('sale.order', 'project_id', string="Sale Orders")
    sale = fields.Many2one('sale.order', string='Sale')
    project_sequence = fields.Char(string='Sequences')
    stock_location_id = fields.Many2one('stock.location', string='Stock Location', store=True)
    sale_order_count = fields.Integer(string='Sale Orders', compute='_compute_sale_order_count')
    seq = fields.Integer('seq')
    is_project_location = fields.Boolean('Is Project location')

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for project in self:
            project.sale_order_count = len(project.sale_order_ids)

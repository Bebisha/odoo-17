from odoo import fields, models, api


class ProjectProject(models.Model):
    _inherit = "project.project"

    bom_line_ids = fields.One2many('bom.line', 'project_id')
    is_bom_line_empty = fields.Boolean(string='Is BOM Line Empty', compute='_compute_is_bom_line_empty')
    sequence = fields.Char()
    bom_count = fields.Integer(compute='compute_bom_count')
    invoice_count = fields.Integer('Invoices', compute='compute_invoice_count')
    variation_invoice_count = fields.Integer('Variation Invoices', compute='compute_variation_invoice_count')


    def compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = False
            sale_order = self.env['sale.order'].search([('project_id', '=', rec.id), ('project_type', '=', 'new')]).ids
            rec.invoice_count = self.env['account.move'].search_count([('sale_order_id', 'in', sale_order)])

    def compute_variation_invoice_count(self):
        for rec in self:
            rec.variation_invoice_count = False
            sale_order = self.env['sale.order'].search(
                [('project_id', '=', rec.id), ('state', 'in', ['done', 'sale']), ('project_type', '!=', 'new')])
            # # rec.variation_ids = False
            # sale_ids = []
            # for order_name in sale_order:
            #     if order_name.name[-1].isalpha():  # Check if the last character is a letter
            #
            #         sale_ids.append(order_name.id)
            rec.variation_invoice_count = self.env['account.move'].search_count([('sale_order_id', 'in', sale_order.ids)])

    @api.depends('bom_line_ids')
    def _compute_is_bom_line_empty(self):
        for record in self:
            record.is_bom_line_empty = bool(record.bom_line_ids)

    def compute_bom_count(self):
        for rec in self:
            rec.bom_count = False
            rec.bom_count = self.env['bom.selection'].search_count([('project_id', '=', rec.id)])

    analytic_count = fields.Integer(string="Analytic Line", compute='compute_analytics_count', )

    def compute_analytics_count(self):
        for record in self:
            record.analytic_count = False
            account_id = self.env['account.analytic.account'].search([('name', '=', self.name)])
            material_request = self.env['material.purchase.requisition'].search([('project_id', '=', self.name)])
            record.analytic_count = self.env['account.analytic.line'].search_count(
                [('account_id', '=', account_id.id), ('material_request_line_ids', 'in', material_request.ids)])

    def action_get_analytic_record(self):
        self.ensure_one()
        account_id = self.env['account.analytic.account'].search([('name', '=', self.name)])
        material_request = self.env['material.purchase.requisition'].search([('project_id', '=', self.name)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Analytic Line',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line',
            'domain': [('account_id', '=', account_id.id), ('material_request_line_ids', 'in', material_request.ids)],
            'context': "{'create': False}"
        }

    # def create_mr(self):
    #     vals = []
    #     for rec in self.bom_line_ids:
    #         vals.append((0, 0, {
    #             'product_id': rec.product_id.id,
    #             'description': rec.product_id.name,
    #             'qty': rec.qty,
    #         }))
    #     mr_id = self.env['material.purchase.requisition'].create({
    #         'department_res_id': 1,
    #         'project_id': self.id,
    #
    #         'requisition_line_ids': vals
    #     })
    #     return {
    #         'name': 'Material Request',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'material.purchase.requisition',
    #         'res_id': mr_id.id,
    #         'context': {'default_project_id': self.id}
    #     }

    def create_variation(self):
        sale_order = self.env['sale.order'].search([('project_id', '=', self.id)], limit=1, order='id DESC')
        return {
            'name': 'Variation',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'context': {'default_project_type': 'existing', 'default_project_id': self.id,
                        'default_partner_id': self.partner_id.id}
        }

    def action_view_bom(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project',
            'view_mode': 'tree,form',
            'res_model': 'bom.selection',
            'context': "{'create':False}",
            'domain': [('project_id', '=', self.id)]
        }

    def action_view_invoices(self):
        self.ensure_one()
        sale_order = self.env['sale.order'].search([('project_id', '=', self.id), ('project_type', '=', 'new')]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'context': "{'create':False}",
            'domain': [('sale_order_id', 'in', sale_order)]
        }

    def action_view_variation_invoices(self):
        self.ensure_one()
        sale_order = self.env['sale.order'].search(
            [('project_id', '=', self.id), ('state', 'in', ['done', 'sale']), ('project_type', '!=', 'new')]).ids
        # rec.variation_ids = False
        # sale_ids = []
        # for order_name in sale_order:
        #     if order_name.name[-1].isalpha():  # Check if the last character is a letter
        #
        #         sale_ids.append(order_name.id)

        # rec.variation_ids = [(6, 0, sale_ids)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Variation Invoices',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'context': "{'create':False}",
            'domain': [('sale_order_id', 'in', sale_order)]
        }

    def create_bom(self):
        return {
            'name': 'Create BOM',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'bom.selection',
            'target': 'current',
            'context': {'default_project_id': self.id}
        }

    # def action_approve(self):
    #     self.create_mr()
    #
    def create_invoice_from_project(self):
        self.ensure_one()
        # action = self.env["ir.actions.actions"]._for_xml_id("action_view_project_invoice_wizard")
        # action['context'] = {
        #     'default_project_id': self.id,
        #
        # }
        # action['domain'] = [('project_id', '=', self.id)]
        # return action
        return {
            'name': 'Create Invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'invoice.project',
            'target': 'new',
            'context': {'default_project_id': self.id},
            'domain': [('project_id', '=', self.id)]
        }


class ProjectBOMLines(models.Model):
    _name = 'bom.line'

    project_id = fields.Many2one('project.project')
    # bom_selection_id = fields.Many2one('bom.selection.line')
    product_category_id = fields.Many2one('product.category', 'Product category',
                                          )
    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float('Quantity')

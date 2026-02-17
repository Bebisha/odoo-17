# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BatchRequisition(models.TransientModel):
    _name = "batch.requisition"
    _description = "Batch Requisition"
    _order = "name desc"

    def _get_mr_domain(self):
        mr_obj = self.env['material.purchase.requisition'].search([('state', '=', 'in_progress')])
        mr_ids = []
        for mr in mr_obj.mapped('requisition_line_ids').filtered(lambda mr_line: mr_line.pr_requisition_id and mr_line.pr_requisition_id.state == 'cancel' or not mr_line.pr_requisition_id):
            mr_ids.append(mr.requisition_id.id)
        return [('id', 'in', mr_ids)]

    user_id = fields.Many2one(
        'res.users', string='Responsible', default=lambda self: self.env.user.id)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.company)
    material_requisition_ids = fields.Many2many(
        'material.purchase.requisition', domain=_get_mr_domain, required=True)
    requisition_line_ids = fields.One2many(
        'batch.requisition.line', 'batch_id', string='Lines')

    @api.onchange('employee_id')
    def change_employee(self):
        if self.employee_id:
            return {'domain': {
                'material_requisition_ids': [('state', '=', 'new'), ('employee_id', 'in', self.employee_id.ids)]}}

    @api.onchange('material_requisition_ids')
    def onchange_material_requisition_ids(self):
        """Update the batch.requisition.line"""
        product_list = []
        selected_mrs = self.material_requisition_ids
        default_branch_lines = self.requisition_line_ids
        batch_lines = [(5, 0, 0)]
        for mr_line in selected_mrs.mapped('requisition_line_ids'):
            if mr_line.pr_requisition_id and mr_line.pr_requisition_id.state == 'cancel' or not mr_line.pr_requisition_id:
                same_product_line = default_branch_lines.filtered(lambda l: l.product_id == mr_line.product_id)
                qty = mr_line.pr_quantity
                mr_ids = mr_line.requisition_id.ids
                if same_product_line:
                    req_lines = selected_mrs.mapped('requisition_line_ids').filtered(lambda l: l.product_id == mr_line.product_id)
                    qty = sum(req_lines.mapped('pr_quantity'))
                    mr_ids = req_lines.mapped('requisition_id').ids
                if mr_line.product_id.id not in product_list:
                    product_list.append(mr_line.product_id.id)
                    batch_lines.append((0, 0, {"product_id": mr_line.product_id.id,
                                               "description": mr_line.description,
                                               "qty": qty,
                                               "uom_id": mr_line.uom_id.id,
                                               "price_unit": mr_line.price_unit,
                                               "requisition_ids": [(6, 0, mr_ids)],
                                               "currency_id": mr_line.currency_id.id}))
        self.write({'requisition_line_ids': batch_lines})

    def create_purchase_requisition(self):
        """Create a purchase requisition from the Batch"""
        purchase_requisitions_obj = self.env['purchase.requisitions']
        for_picking = []

        if not self.material_requisition_ids:
            raise UserError("Please select at least one material requisition order")
        if not self.requisition_line_ids:
            raise UserError("Please select at least one product order")
        employee_id = self.employee_id
        vals = {
            'employee_id': employee_id.id,
            'requisition_responsible_id': self.user_id.id,
            'requisition_date': fields.Datetime.now(),
            'state': 'new',
            'company_id': self.env.company.id,
            'currency_id': self.env.company.currency_id.id,
            'is_batch_req': True,
            # 'picking_type_id': self.material_requisition_ids.mapped('picking_type_id')[0].id,
        }
        pur_requisition = purchase_requisitions_obj.create(vals)
        for batch_line in self.requisition_line_ids:
            mr_req_lines = self.requisition_line_ids.mapped('requisition_ids').mapped('requisition_line_ids').filtered(lambda l: l.product_id == batch_line.product_id)
            for line in mr_req_lines:
                line.requisition_id.pr_ids |= pur_requisition
                if line.product_id.qty_available:
                    for_picking.append({'product_id': line.product_id.id, 'line': line})
                line.demand_qty = line.pr_quantity
                line.pr_requisition_id = pur_requisition.id

        if self.env.context.get('open_purchase_requisition'):
            return self.action_view_purchase_requisition(pur_requisition)

        return {'type': 'ir.actions.act_window_close'}

    def action_view_purchase_requisition(self, pur_requisition_id):
        """Redirect to the purchase requisitions related to the current batch"""
        return {
            'name': 'Purchase Requisition',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.requisitions',
            'res_id': pur_requisition_id.id,
            'context': {'default_purchase_requisition_id': pur_requisition_id.id},
            'target': 'current'
        }


class BatchRequisitionLine(models.TransientModel):
    _name = "batch.requisition.line"
    _description = "Batch Requisition Line"

    product_id = fields.Many2one('product.product', string="Product")
    description = fields.Text(string="Description", required=True)
    qty = fields.Float(string="Quantity")
    available_qty = fields.Float(string="Available Quantity", related='product_id.qty_available')
    uom_id = fields.Many2one('uom.uom', string="Unit Of Measure")
    batch_id = fields.Many2one('batch.requisition', string="Batch Requisition")
    price_unit = fields.Monetary("Unit Price")
    currency_id = fields.Many2one('res.currency', string='Currency')
    requisition_ids = fields.Many2many('material.purchase.requisition', string="MRs", copy=False)

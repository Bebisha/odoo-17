# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class BatchRequisition(models.TransientModel):
    _name = "batch.pr.requisition"
    _description = "Batch PR Requisition"
    _order = "name desc"

    user_id = fields.Many2one(
        'res.users', string='Responsible', default=lambda self: self.env.user.id)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.company)
    vendor_ids = fields.Many2many('res.partner', string='Vendor')
    pr_requisition_ids = fields.Many2many(
        'purchase.requisitions', required=True, domain="[('state', '=', 'in_progress')]")
    requisition_line_ids = fields.One2many(
        'batch.pr.requisition.line', 'batch_id', string='Lines', )

    @api.onchange('pr_requisition_ids')
    def onchange_pr_requisition_ids(self):
        """Update the batch.pr.requisition.line"""
        product_list = []
        selected_prs = self.pr_requisition_ids
        default_branch_lines = self.requisition_line_ids
        batch_lines = [(5, 0, 0)]
        for pr_line in selected_prs.mapped('requisition_line_ids').filtered(lambda p: all(x.state == 'cancel' for x in p.po_ids.mapped('state')) or not p.po_ids):
            same_product_line = default_branch_lines.filtered(lambda l: l.product_id == pr_line.product_id)
            qty = pr_line.demand_qty
            pr_ids = pr_line.pr_requisition_id.ids
            pr_line_ids = pr_line.ids
            if same_product_line:
                req_lines = selected_prs.mapped('requisition_line_ids').filtered(
                    lambda l: l.product_id == pr_line.product_id)
                qty = sum(req_lines.mapped('demand_qty'))
                pr_ids = req_lines.mapped('pr_requisition_id').ids
                pr_line_ids = req_lines.ids
            if pr_line.product_id.id not in product_list:
                product_list.append(pr_line.product_id.id)
                batch_lines.append((0, 0, {"product_id": pr_line.product_id.id,
                                           "description": pr_line.description,
                                           "qty": qty,
                                           "uom_id": pr_line.uom_id.id,
                                           "price_unit": pr_line.price_unit,
                                           "pr_requisition_ids": [(6, 0, pr_ids)],
                                           "pr_req_line_ids": [(6, 0, pr_line_ids)],
                                           "currency_id": pr_line.currency_id.id}))
        self.write({'requisition_line_ids': batch_lines})

    # @api.onchange('pr_requisition_ids')
    # def onchange_pr_requisition_ids(self):
    #     """Update the batch.pr.requisition.line"""
    #     if self.pr_requisition_ids:
    #         product_list = []
    #         batch_lines = [(5, 0, 0)]
    #         for line in self.pr_requisition_ids.mapped('requisition_line_ids'):
    #             same_product_line = self.pr_requisition_ids.mapped('requisition_line_ids').filtered(
    #                 lambda l: l.product_id == line.product_id)
    #             if line.product_id.id not in product_list:
    #                 product_list.append(line.product_id.id)
    #                 batch_lines.append((0, 0, {"product_id": line.product_id.id,
    #                                            "description": line.description,
    #                                            "qty": sum(same_product_line.mapped('qty')),
    #                                            "uom_id": line.uom_id.id,
    #                                            "price_unit": line.price_unit,
    #                                            "currency_id": line.currency_id.id}))
    #         self.write({'requisition_line_ids': batch_lines})

    def create_po_requisition(self):
        if not self.pr_requisition_ids:
            raise UserError("Please select at least one Purchase requisition order")
        if not self.requisition_line_ids:
            raise UserError("Please select at least one product order")

        name = self.pr_requisition_ids.mapped('sequence')
        sequence = ', '.join(name)
        po_ids = []
        for vendor in self.vendor_ids:
            purchase_order_obj = self.env['purchase.order'].sudo()
            rfq_lines = []
            pr_ids = []
            for line in self.requisition_line_ids:
                for p in line.pr_requisition_ids:
                    pr_ids.append(p.id)
                po_line_vals = {
                    'product_id': line.product_id.id,
                    'product_qty': line.qty,
                    'name': line.description if line.description else ' ',
                    'price_unit': line.price_unit,
                    'date_planned': fields.Datetime.now(),
                    'req_line_ids': [(6, 0, line.pr_req_line_ids.ids)],
                    'product_uom': line.uom_id.id,
                }
                rfq_lines.append((0, 0, po_line_vals))
            po = purchase_order_obj.sudo().create({
                'partner_id': vendor.id,
                'date_order': fields.Datetime.now(),
                'state': 'draft',
                'order_line': rfq_lines,
                'company_id': self.company_id.id,
                'pr_requisition_ids': [(6, 0, pr_ids)],
                'origin': sequence,
                'estimation_id': [rec.estimation_id.id for rec in self.pr_requisition_ids if rec.estimation_id]

            })

            po_ids.append(po.id)
        alternative_po = self.env['purchase.order'].search(
            [('origin', '=', sequence), ('partner_id', 'in', self.vendor_ids.ids)])
        alternate_lines = []
        for alt in alternative_po:
            alt_line_vals = {
                'partner_id': alt.partner_id,
                'name': alt.name,
                'date_planned': alt.date_planned,
                'amount_total': alt.amount_total,
                'state': alt.state,
            }
            alternate_lines.append((0, 0, alt_line_vals))
        alternative_po.write({
            'alternative_po_ids': alternate_lines,
        })
        pr_ids = []
        for rec in self.pr_requisition_ids:
            pr_ids.append(rec.id)
        alternative_po.write({'pr_requisition_ids': [(6, 0, pr_ids)]})

        for req in self.pr_requisition_ids:
            req.state = 'done'
        self.requisition_line_ids.mapped('pr_req_line_ids').write({'po_ids': [(6, 0, po_ids)]})
        return self.action_view_purchase(po_ids)

    def action_view_purchase(self, po_ids):
        """Redirect to the purchase requisitions related to the current batch"""
        if len(po_ids) != 1:
            return {
                'name': 'Purchase Order',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'purchase.order',
                'domain': [('id', 'in', po_ids)],
            }
        else:
            return {
                'name': 'Purchase Order',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'res_id': po_ids[0],
                'target': 'current'
            }


class BatchPRRequisitionLine(models.TransientModel):
    _name = "batch.pr.requisition.line"
    _description = "Batch PR Requisition Line"

    product_id = fields.Many2one('product.product', string="Product")
    description = fields.Text(string="Description", required=True)
    qty = fields.Float(string="Quantity")
    available_qty = fields.Float(string="Available Quantity", related='product_id.qty_available')
    uom_id = fields.Many2one('uom.uom', string="Unit Of Measure")
    batch_id = fields.Many2one('batch.pr.requisition', string="Batch PR Requisition")
    price_unit = fields.Monetary("Unit Price")
    currency_id = fields.Many2one('res.currency', string='Currency')
    pr_requisition_ids = fields.Many2many(
        'purchase.requisitions', required=True)
    pr_req_line_ids = fields.Many2many(
        'requisition.line', required=True)

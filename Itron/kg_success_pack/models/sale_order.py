# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    success_pack_line_ids = fields.One2many('kg.success.pack.line', 'sale_id', string='Success Pack Lines')
    success_pack = fields.Boolean(string="Success Pack", default=False,)
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date', related='pack_project_id.end_date',readonly=True)
    estimated_hours = fields.Float(related="success_pack_id.hours", string='Planned Hours')
    worked_hours = fields.Float(string='Worked Hours', compute="compute_spent_hours")
    remaining_hours = fields.Float(string='Remaining Hours', compute="compute_spent_hours")
    success_pack_id = fields.Many2one('kg.success.pack', 'Success Package')
    pack_project_id = fields.Many2one('pack.projects', string='Pack Project', )
    pm_id = fields.Many2one('hr.employee', string='Project Manager')
    pack_project_id_state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('hold', 'Hold'),
        ('closed', 'Closed'),
    ],
        string='Project Status',
        related='pack_project_id.stages',
        default='draft',
    )
    is_fully_paid = fields.Boolean(default=False,compute='compute_payment_status')
    kg_partner_id = fields.Many2one('res.partner',compute='compute_kg_partner')

    @api.depends('partner_id')
    def compute_kg_partner(self):
        for rec in self:
            if rec.success_pack:
                rec.kg_partner_id = rec.partner_id.id
            else:
                rec.kg_partner_id = False

    @api.depends('invoice_ids.amount_residual', 'invoice_ids.amount_total')
    def compute_payment_status(self):
        for record in self:
            if self.invoice_ids:
                invoices = record.invoice_ids
                total_invoiced = sum(inv.amount_total for inv in invoices)
                all_paid = all(inv.amount_residual == 0 for inv in invoices)
                record.is_fully_paid = all_paid and total_invoiced == record.amount_total
            else:
                record.is_fully_paid = False

    @api.onchange('start_date')
    def onchange_start_date(self):
        for rec in self:
            if rec.start_date:
                rec.end_date = rec.start_date + relativedelta(years=1, days=-1)

    @api.depends('start_date', 'end_date', 'pack_project_id')
    @api.onchange('start_date', 'end_date', 'pack_project_id')
    def compute_spent_hours(self):
        print("gggg")
        for rec in self:
            timesheets = self.env['account.analytic.line'].sudo().search([('date', '>=', rec.start_date),
                                                                          ('date', '<=', rec.end_date),
                                                                          ('partner_id', '=', rec.partner_id.id),
                                                                          ('task_id.success_pack_id', '=',
                                                                           rec.success_pack_id.id)])
            rec.worked_hours = sum(timesheets.mapped('unit_amount'))
            rec.remaining_hours = rec.estimated_hours - rec.worked_hours
            print("rec.remaining_hours1",rec.remaining_hours)

    @api.onchange('success_pack', 'success_pack_id')
    def create_sale_line(self):
        for order in self:
            if order.success_pack and order.success_pack_id:
                product = order.success_pack_id.product_id

                if not product:
                    raise ValidationError("No product set on the selected Success Pack.")

                existing_line = order.order_line.filtered(lambda l: l.product_id == product)

                if not existing_line:
                    # Clear existing lines
                    order.order_line = [(5, 0, 0)]

                    # Add the new line
                    order.order_line = [(0, 0, {
                        'product_id': product.id,
                        'name': product.name,
                        'product_uom_qty': 1,
                        'price_unit': product.lst_price,
                        'product_uom': product.uom_id.id,
                        'success_line': True,
                    })]
            else:
                order.order_line = [(5, 0, 0)]


    def create_project_button(self):
        self.ensure_one()
        if not self.pm_id:
            raise ValidationError('Please add a Project Manager')
        sequence = self.env['ir.sequence'].next_by_code('success.pack.sequence')

        partner_first_name = self.partner_id.name.split(' ')[0] if self.partner_id.name else ''

        project_name = f"{sequence} {partner_first_name}".strip()

        new_project = self.env['pack.projects'].create({
            'partner_id': self.partner_id.id,
            'name': project_name,
            'start_date': self.start_date,
            'sale_id': self.id,
            'end_date': self.end_date if self.end_date else self.start_date + relativedelta(years=1,days=-1),
            'estimated_hours': self.estimated_hours,
            'pm_id': self.pm_id.id,
            'order_date': self.date_order,
            'success_pack_id': self.success_pack_id.id,
        })
        self.pack_project_id = new_project.id

        if self.pm_id.work_email:
            mail_values = {
                'subject': f"New Success Pack Project Assigned: {sequence}",
                'body_html': f"""
                        <p>Dear {self.pm_id.name},</p>
                        <p>A new Success Pack project has been created and assigned to you.</p>
                        <p><strong>Project Name:</strong> {sequence}<br/>
                        <strong>Start Date:</strong> {self.start_date}<br/>
                        <strong>End Date:</strong> {self.end_date}</p>
                        <p>Regards,<br/>Success Pack Team</p>
                    """,
                'email_to': self.pm_id.work_email,
                'auto_delete': True,
            }
            self.env['mail.mail'].create(mail_values).send()

        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Project',
        #     'res_model': 'pack.projects',
        #     'view_mode': 'form',
        #     'res_id': new_project.id,
        #     'target': 'current',
        # }

    def action_show_project_pack(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project',
            'res_model': 'pack.projects',
            'view_mode': 'form',
            'res_id': self.pack_project_id.id,
            'target': 'current',
        }

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    success_line = fields.Boolean(string='Success Line', readonly=True)

    @api.model
    def create(self, vals):
        order_id = vals.get('order_id')

        if order_id:
            order = self.env['sale.order'].browse(order_id)

            if order.success_pack:
                if order.order_line:
                    raise ValidationError("You cannot add more lines when Success Pack is enabled.")

        return super().create(vals)

    @api.model
    def write(self, vals):
        for line in self:
            order = line.order_id
            if order.success_pack and len(order.order_line) > 1:
                raise ValidationError("Modifying lines is not allowed when Success Pack is enabled.")
        return super().write(vals)

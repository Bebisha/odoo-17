from ast import literal_eval
from collections import defaultdict
from odoo import models, fields
from odoo.osv import expression
from odoo.tools.misc import unquote
from odoo import models, api, _
from odoo.exceptions import ValidationError

class KGProjectTaskInherit(models.Model):
    _inherit = "project.task"

    subtask_total_hours = fields.Float(
        string="Subtask Total Hours",
        compute="_compute_subtask_total_hours",
    )

    @api.depends('child_ids.allocated_hours')
    def _compute_subtask_total_hours(self):
        for task in self:
            task.subtask_total_hours = sum(
                task.child_ids.mapped('allocated_hours')
            )

    @api.constrains('allocated_hours', 'child_ids.allocated_hours')
    def _check_main_vs_subtask_hours(self):
        for task in self:
            if not task.child_ids:
                continue

            total_subtask_hours = sum(task.child_ids.mapped('allocated_hours'))
            if not task.allocated_hours:
                continue

            if task.allocated_hours > total_subtask_hours:
                raise ValidationError(_(
                    "Main item planned hours (%s) cannot be less than "
                    "the total sub-item hours (%s)."
                ) % (
                                          task.allocated_hours,
                                          total_subtask_hours
                                      ))

    def _get_subtask_total(self):
        self.ensure_one()
        return sum(self.child_ids.mapped('allocated_hours'))

    @api.onchange('child_ids.allocated_hours')
    def _onchange_child_hours_update_parent(self):
        for task in self:
            if task.child_ids:
                task.allocated_hours = task._get_subtask_total()

    @api.model
    def create(self, vals):
        task = super().create(vals)

        if task.parent_id:
            task.parent_id.allocated_hours = task.parent_id._get_subtask_total()

        return task

    def write(self, vals):
        res = super().write(vals)

        for task in self:
            if task.parent_id:
                parent = task.parent_id
                parent.allocated_hours = parent._get_subtask_total()

        return res

    def _domain_sale_line_id(self):
        domain = expression.AND([
            self.env['sale.order.line']._sellable_lines_domain(),
            [
                '|',
                ('order_partner_id.commercial_partner_id.id', 'parent_of', unquote('partner_id if partner_id else []')),
                ('order_partner_id', '=?', unquote('partner_id')),
                ('is_service', '=', True), ('is_expense', '=', False)
            ],
        ])
        return domain

    enquiry_id = fields.Many2one("crm.lead", string="Enquiry", related="project_id.enquiry_id")
    estimation_id = fields.Many2one("crm.estimation", string="Estimation", related="enquiry_id.estimation_id")

    job_no = fields.Char(string="Job No", compute="compute_job_no", store=True)
    vessel_id = fields.Many2one("vessel.code", string="Vessel", related="sale_order_id.vessel_id", store=True)
    remarks = fields.Text(string="Remarks")
    coordinator_ids = fields.Many2many("res.users", "coordinator_rel", string="Coordinators",
                                       context={'active_test': False}, tracking=True,
                                       domain="[('share', '=', False), ('active', '=', True)]")

    start_date = fields.Datetime(string="Start Date", related="planned_date_start", store=True)

    def compute_job_no(self):
        for rec in self:
            rec.job_no = False
            if rec.sale_order_id:
                rec.job_no = rec.sale_order_id.name

    def _ensure_sale_order_linked(self, sol_ids):
        """ Orders created from project/task are supposed to be confirmed to match the typical flow from sales, but since
        we allow SO creation from the project/task itself we want to confirm newly created SOs immediately after creation.
        However this would leads to SOs being confirmed without a single product, so we'd rather do it on record save.
        """
        quotations = self.env['sale.order.line'].sudo()._read_group(
            domain=[('state', '=', 'draft'), ('id', 'in', sol_ids), ('previous_sol_id', '=', False)],
            aggregates=['order_id:recordset'],
        )[0][0]
        # if quotations:
        #     quotations.action_confirm()

    def action_create_invoice(self):
        # ensure the SO exists before invoicing, then confirm it
        so_to_confirm = self.filtered(
            lambda task: task.sale_order_id and task.sale_order_id.state in ['draft', 'sent']
        ).mapped('sale_order_id')
        if so_to_confirm:
            so_to_confirm.qtn_approved = True
            so_to_confirm.is_approval_required = False
            so_to_confirm.action_confirm()

        # redirect create invoice wizard (of the Sales Order)
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_view_sale_advance_payment_inv")
        context = literal_eval(action.get('context', "{}"))
        so_task_mapping = defaultdict(list)
        for task in self:
            if task.sale_order_id:
                # As the key is anyway stringified in the JS, we casted the key here to make it clear.
                so_task_mapping[str(task.sale_order_id.id)].append(task.id)
        context.update({
            'active_id': self.sale_order_id.id if len(self) == 1 else False,
            'active_ids': self.mapped('sale_order_id').ids,
            'industry_fsm_message_post_task_id': so_task_mapping,
        })
        action['context'] = context
        return action

    def action_fsm_validate(self, stop_running_timers=False):
        """ If allow billable on task, timesheet product set on project and user has privileges :
            Create SO confirmed with time and material.
        """
        res = super().action_fsm_validate(stop_running_timers)
        if res is True:
            billable_tasks = self.filtered(
                lambda task: task.allow_billable and (task.allow_timesheets or task.allow_material))
            timesheets_read_group = self.env['account.analytic.line'].sudo()._read_group(
                [('task_id', 'in', billable_tasks.ids), ('project_id', '!=', False)], ['task_id'], ['__count'])
            timesheet_count_by_task_dict = {task.id: count for task, count in timesheets_read_group}
            for task in billable_tasks:
                timesheet_count = timesheet_count_by_task_dict.get(task.id)
                if not task.sale_order_id and not timesheet_count:  # Prevent creating/confirming a SO if there are no products and timesheets
                    continue
                task._fsm_ensure_sale_order()
                if task.allow_timesheets:
                    task._fsm_create_sale_order_line()
                if task.sudo().sale_order_id.state in ['draft', 'sent']:
                    task.sudo().sale_order_id.qtn_approved = True
                    task.sudo().sale_order_id.is_approval_required = False
                    task.sudo().sale_order_id.action_confirm()
            billable_tasks._prepare_materials_delivery()
        return res

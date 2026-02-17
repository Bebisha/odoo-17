from odoo import models, fields
from odoo.osv import expression
from odoo.tools.misc import unquote


class KGProjectProjectInherit(models.Model):
    _inherit = "project.project"

    def _domain_sale_line_id(self):
        domain = expression.AND([
            self.env['sale.order.line']._sellable_lines_domain(),
            [
                ('is_service', '=', True),
                ('is_expense', '=', False),
                ('order_partner_id', '=?', unquote("partner_id")),
            ],
        ])
        return domain

    enquiry_id = fields.Many2one("crm.lead", string="Enquiry")
    estimation_id = fields.Many2one("crm.estimation", string="Estimation", related="enquiry_id.estimation_id")
    labour_cost_id = fields.Many2one("crm.labour.cost", string="Labour Id")
    estimated_hours = fields.Float(string="Estimated Hours",compute="compute_estimated_hours")
    project_team_id = fields.Many2one('project.team', sting="Project Teams")
    Coordinator_id = fields.Many2one('hr.employee', sting="Coordinator")
    qc_id = fields.Many2one('hr.employee', sting="QC")
    team_member_ids = fields.Many2many('hr.employee', 'proj_tem_id', string='Team Members', copy=False,related='project_team_id.team_member_ids', readonly=False)

    def _ensure_sale_order_linked(self, sol_ids):
        """ Orders created from project/task are supposed to be confirmed to match the typical flow from sales, but since
        we allow SO creation from the project/task itself we want to confirm newly created SOs immediately after creation.
        However this would leads to SOs being confirmed without a single product, so we'd rather do it on record save.
        """
        quotations = self.env['sale.order.line'].sudo()._read_group(
            domain=[('state', '=', 'draft'), ('id', 'in', sol_ids),('previous_sol_id','=',False)],
            aggregates=['order_id:recordset'],
        )[0][0]
        # if quotations:
        #     quotations.action_confirm()

    def compute_estimated_hours(self):
        for rec in self:
            if rec.estimation_id and rec.estimation_id.labour_cost_ids:
                rec.estimated_hours = sum(rec.estimation_id.labour_cost_ids.mapped('quantity'))
            else:
                rec.estimated_hours = 0.00

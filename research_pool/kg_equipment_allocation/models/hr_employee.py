# -*- encoding: utf-8 -*-


from odoo import _, fields, models


class HrEmployee(models.Model):

    _inherit = "hr.employee"



    personal_equipment_ids = fields.One2many(
        comodel_name="hr.personal.equipment",
        inverse_name="employee_id",
        domain=[("state", "not in", ["draft", "cancelled"])],
    )

    equipment_request_count = fields.Integer(
        compute="_compute_equipment_request_count",
    )

    personal_equipment_count = fields.Integer(
        compute="_compute_personal_equipment_count"
    )


    def _compute_personal_equipment_count(self):
        self.personal_equipment_count = len(self.personal_equipment_ids)


    def action_open_personal_equipment(self):
        self.ensure_one()
        return {
            "name": _("Personal Equipment"),
            "type": "ir.actions.act_window",
            "res_model": "hr.personal.equipment",
            "context": {"group_by": "state"},
            "view_mode": "tree,form",
            "domain": [("id", "in", self.personal_equipment_ids.ids)],
        }
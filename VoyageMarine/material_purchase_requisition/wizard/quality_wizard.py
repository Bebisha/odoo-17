from markupsafe import Markup

from odoo import models, fields, api


class QualityCheckWizard(models.TransientModel):
    _name = 'quality.check.wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Quality Check Wizard'

    add_note = fields.Text(string="Additional Note", help="The Product is not good", default=False)
    is_pass = fields.Boolean(string="Passed", default=False)
    is_fail_reason = fields.Boolean(string="Failed")
    is_fail = fields.Boolean(string="Failed")
    wiz_id = fields.Many2one('material.purchase.requisition', string="MR")
    # team_id = fields.Many2one('quality.alert.team', string="Team")

    def action_pass(self):
        for rec in self:
            if rec.wiz_id:
                rec.wiz_id.is_quality = True
                rec.wiz_id.ensure_one()
                body = Markup("<strong>Additional Note : </strong><br>%(reason)s") % {'reason': rec.add_note}
                rec.wiz_id.message_post(body=body)

                # team = self.env['quality.alert.team'].search([], limit=1)

                # for line in rec.wiz_id.requisition_line_ids:
                    # record_pass = self.env['quality.check'].create({
                    #     'product_id': line.product_id.id,
                    #     'partner_id': rec.wiz_id.employee_id,
                    #     'quality_state': 'pass',
                    #     'note': rec.add_note,
                    #     'picking_id': rec.wiz_id.id,
                    #     'test_type_id': 7,
                    #     'team_id': team.id if team else False  # Set team_id if found
                    # })

            self.is_pass = True

    def action_fail(self):
        for rec in self:
            if rec.wiz_id:
                rec.wiz_id.is_quality = True
                rec.wiz_id.ensure_one()
                body = Markup("<strong>Additional Note : </strong><br>%(reason)s") % {'reason': rec.add_note}
                rec.wiz_id.message_post(body=body)
            rec.wiz_id.state = 'cancel'
            # test_type = self.env['quality.point.test_type'].search([])
            # team = self.env['quality.alert.team'].search([], limit=1)
            # employee_id = rec.employee_id.id if rec.employee_id else False
            # for line in rec.wiz_id.requisition_line_ids:
            #     self.env['quality.check'].create({
            #         'product_id': line.product_id.id,
            #         # 'partner_id': employee_id,
            #
            #         'quality_state': 'fail',
            #         'note': rec.add_note,
            #         'picking_id': rec.wiz_id.id,
            #         'test_type_id': 7,
            #         'team_id': team.id if team else False
            #     })

            self.is_fail = True


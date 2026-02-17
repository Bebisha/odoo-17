from odoo import models, fields, _


class RevisionReasonWizard(models.TransientModel):
    _name = 'revision.reason.wizard'
    _description = 'Sale Order Cancellation Reasons'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    sale_id = fields.Many2one("sale.order", string="Sales Reference")
    revision_reason = fields.Text(string="Reason")
    is_reject = fields.Boolean(default=False, string="Is Reject")

    def confirm_reject_reason(self):
        if self.sale_id:
            self.sale_id.action_reject()
            self.sale_id.rejected_reason = self.revision_reason

    def create_revision(self):
        if not self.sale_id.main_revision_id:
            self.sale_id.main_revision_id = self.sale_id.id
        else:
            self.sale_id.main_revision_id = self.sale_id.main_revision_id

        self.sale_id.state = 'cancel'

        self.sale_id.created_revision = True

        order_line = []
        revision_count = 0

        so_name = self.sale_id.without_revision_qtn

        revision_ids = self.env['sale.order'].search([('main_revision_id', '=', self.sale_id.main_revision_id.id)])
        if revision_ids:
            revision_count = len(revision_ids)

        for line in self.sale_id.order_line:
            line_vals = (0, 0, {
                'name': line.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'product_uom': line.product_uom.id,
                'tax_id': line.tax_id.ids,
                'qty_delivered': line.qty_delivered,
                'copy_delivered_qty': line.qty_delivered,
                'display_type': line.display_type,
                'invoice_lines': line.invoice_lines,
                'is_jobsheet': line.is_jobsheet,
                'is_items': line.is_items,
                'code': line.code,
                'previous_sol_id': line.id,
                'is_product_select': line.is_product_select,
                'is_add': line.is_add,
                'is_subitem': line.is_subitem,
                'sl_no': line.sl_no,
            })
            order_line.append(line_vals)

        vals = {
            'name': so_name + '_R' + str(revision_count),
            'state': 'draft',
            'order_line': order_line,
            'main_revision_id': self.sale_id.main_revision_id.id,
            'revision_count': revision_count,
            'revision_ids': [(6, 0, revision_ids.ids)],
            'so_confirmed': self.sale_id.so_confirmed,
            'quotation_reference': self.sale_id.quotation_reference,
            'so_reference': self.sale_id.so_reference,
            'calibration_id': self.sale_id.calibration_id.id,
            'lsa_id': self.sale_id.lsa_id.id,
            'ffa_id': self.sale_id.ffa_id.id,
            'navigation_id': self.sale_id.navigation_id.id,
            'field_service_id': self.sale_id.field_service_id.id,
            'calibration_form_count': self.sale_id.calibration_form_count,
            'lsa_form_count': self.sale_id.lsa_form_count,
            'ffa_form_count': self.sale_id.ffa_form_count,
            'field_service_form_count': self.sale_id.field_service_form_count,
            'navigation_communication_form_count': self.sale_id.navigation_communication_form_count,
            'created_revision': False,
            'estimation_id': self.sale_id.estimation_id.id,
            'forms_created': True,
            'without_revision_qtn': self.sale_id.without_revision_qtn,
            'customer_reference': self.sale_id.customer_reference,
            'client_order_ref': self.sale_id.client_order_ref,
            'purchase_reference': self.sale_id.purchase_reference,
            'journal_id': self.sale_id.journal_id.id,
            'partner_bank_id': self.sale_id.partner_bank_id.id,
            'survey_id': self.sale_id.survey_id.id,
            'analytic_account_id': self.sale_id.analytic_account_id.id,
            'commitment_date': self.sale_id.commitment_date,
            'terms_conditions_id': self.sale_id.terms_conditions_id.id,
            'delivery_terms_id': self.sale_id.delivery_terms_id.id,
            'note': self.sale_id.note,
            'delivery_terms_condition': self.sale_id.delivery_terms_condition,
        }

        copy_id = self.sale_id.copy(default=vals)
        copy_id.calibration_id.saleorder_id = copy_id.id
        copy_id.lsa_id.saleorder_id = copy_id.id
        copy_id.revision_id = copy_id.id
        copy_id.ffa_id.saleorder_id = copy_id.id
        copy_id.navigation_id.saleorder_id = copy_id.id
        copy_id.field_service_id.saleorder_id = copy_id.id

        copy_id.invoice_ids.write({'invoice_origin': copy_id.name})
        if copy_id.estimation_id:
            copy_id.estimation_id.write({
                'so_ids': [(4, copy_id.id)]
            })
        self.sale_id.sale_revision_reason = self.revision_reason

        calibration_id = self.env['calibration.form'].search([('saleorder_id', '=', self.sale_id.id)])
        if calibration_id:
            calibration_id.write({'saleorder_id': copy_id})

        lsa_id = self.env['lsa.form'].search([('saleorder_id', '=', self.sale_id.id)])
        if lsa_id:
            lsa_id.write({'saleorder_id': copy_id})

        ffa_id = self.env['ffa.form'].search([('saleorder_id', '=', self.sale_id.id)])
        if ffa_id:
            ffa_id.write({'saleorder_id': copy_id})

        navigation_id = self.env['navigation.communication'].search([('saleorder_id', '=', self.sale_id.id)])
        if navigation_id:
            navigation_id.write({'saleorder_id': copy_id})

        field_service_id = self.env['field.service'].search([('saleorder_id', '=', self.sale_id.id)])
        if field_service_id:
            field_service_id.write({'saleorder_id': copy_id})

        cal_repair_ids = self.env['repair.order'].search([('saleorder_id', '=', self.sale_id.id)])

        repair_ids = self.env['repair.order'].search(
            [('saleorder_id', '=', self.sale_id.id), ('revision_created', '=', False)])
        for repair_id in repair_ids:
            order_lines = []
            order_lines_note = []
            product_names = []

            for repair_line in repair_id.move_ids:
                product = repair_line.product_id
                product_names.append(product.name)
                order_line_data = {
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom_qty': repair_line.product_uom_qty,
                    'order_id': copy_id.id,
                    'price_unit': product.lst_price,
                    'is_add': True,
                    'is_subitem':True
                    # 'line_readonly': True,
                    # 'is_product_select': False
                }
                order_lines.append(order_line_data)
                repair_line.repair_id.revision_created = True

            main_product_name = repair_id.product_id.name if repair_id.product_id else "unknown product"
            comment = (
                f"The main product repaired is: {main_product_name}. "
                f"The following products were repaired using parts: {', '.join(product_names)} for calibration."
            )
            order_line_note = {
                'name': comment,
                'display_type': 'line_note',
                'product_id': False,
                'product_uom_qty': 0,
                'product_uom': False,
                'price_unit': 0,
                'order_id': copy_id.id,
                'tax_id': False,
            }
            order_lines_note.append(order_line_note)

            if order_lines:
                self.env['sale.order.line'].create(order_lines_note)
                created_lines = self.env['sale.order.line'].create(order_lines)
                # for created_line in created_lines:
                #     related_repair_lines = repair_id.move_ids.filtered(lambda r: r.product_id == created_line.product_id)
                #     for related_repair_line in related_repair_lines:
                #         related_repair_line.sale_line_id = created_lines.id

        if cal_repair_ids:
            cal_repair_ids.write({'saleorder_id': copy_id.id})

        mrp_ids = self.env['mrp.production'].search([('origin', '=', self.sale_id.name)])
        if mrp_ids:
            mrp_ids.write({'origin': copy_id.name, 'sale_id': copy_id.id})

        if self.sale_id.picking_ids:
            self.sale_id.picking_ids.write({
                'sale_id': copy_id.id,
                'so_ids': [(6, 0, copy_id.ids)]
            })

        for new_line in copy_id.order_line:
            if not new_line.is_jobsheet:
                if new_line.product_id.detailed_type == 'service':
                    project_ids = self.env['project.project'].search(
                        [('sale_line_id', '=', new_line.previous_sol_id.id)])
                    if project_ids:
                        for proj in project_ids:
                            proj.sale_line_id = new_line.id

                    milestone_ids = self.env['project.milestone'].search(
                        [('sale_line_id', '=', new_line.previous_sol_id.id)])
                    if milestone_ids:
                        for mil in milestone_ids:
                            mil.sale_line_id = new_line.id

                    task_ids = self.env['project.task'].search([('sale_line_id', '=', new_line.previous_sol_id.id)])
                    if task_ids:
                        if not new_line.previous_sol_id.is_expense and new_line.previous_sol_id.is_service:
                            for task in task_ids:
                                task.sale_line_id = new_line.id
                                task.sale_order_id = copy_id.id

                else:
                    stock_move_ids = self.env['stock.move'].search([('sale_line_id', '=', new_line.previous_sol_id.id)])
                    if stock_move_ids:
                        for sm in stock_move_ids:
                            sm.sale_line_id = new_line.id

            else:
                new_line.qty_delivered = new_line.copy_delivered_qty

        view_id = self.env.ref('sale.view_order_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('sale Order'),
            'res_model': 'sale.order',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_id': copy_id.id,
        }

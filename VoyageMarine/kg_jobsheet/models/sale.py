from docopt import Required
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.populate import compute
import warnings


class KGSaleOrder(models.Model):
    _inherit = "sale.order"
    _description = 'Quotation'

    calibration_form_count = fields.Integer(
        string="Calibration Form Count",
        compute="_compute_form_counts"
    )
    lsa_form_count = fields.Integer(
        string="LSA Form Count",
        compute="_compute_form_counts"
    )
    ffa_form_count = fields.Integer(
        string="FFA Form Count",
        compute="_compute_form_counts"
    )
    field_service_form_count = fields.Integer(
        string="FIELD_SERVICE Form Count",
        compute="_compute_form_counts"
    )
    navigation_communication_form_count = fields.Integer(
        string="Navigation and Communication Form Count",
        compute="_compute_form_counts"
    )
    is_complete_saleoder = fields.Boolean(string="Is Saleorder", default=False, copy=False)
    is_not_product_calibration = fields.Boolean(string="Is Saleorder", default=False, copy=False)
    forms_created = fields.Boolean(default=False, copy=False)

    calibration_id = fields.Many2one("calibration.form", string="Calibration")
    lsa_id = fields.Many2one("lsa.form", string="LSA")
    ffa_id = fields.Many2one("ffa.form", string="FFA")
    navigation_id = fields.Many2one("navigation.communication", string="Navigation")
    field_service_id = fields.Many2one("field.service", string="Field Service")

    job_sheet_no = fields.Char(string="Job Sheet no", copy=False, index=True, readonly=False,
                               default=lambda self: _('New'))
    job_delivery_note = fields.Char(string="Delivery Note", copy=False, index=True, readonly=False,
                               default=lambda self: _('New'))

    calibrate_repair_ids = fields.Many2many("repair.order", string="Calibrate Repairs",
                                            compute="compute_calibrate_repair_ids")

    repair_count = fields.Integer(compute='get_count')
    ser_delivery_count = fields.Integer(compute='get_count')

    def get_count(self):
        for rec in self:
            rec.repair_count = self.env['repair.order'].search_count([('saleorder_id', '=', self.id)])
            rec.ser_delivery_count = self.env['stock.picking'].search_count([('lead_id', '=',self.opportunity_id.id ),('repair_id','!=',False)])


    def compute_calibrate_repair_ids(self):
        for rec in self:
            repair_ids = self.env['repair.order'].search([('saleorder_id', '=', rec.id)])
            if repair_ids:
                rec.calibrate_repair_ids |= repair_ids
            else:
                rec.calibrate_repair_ids = False

    # def action_confirm(self):
    #     res = super(KGSaleOrder, self).action_confirm()
    #
    #     for order in self:
    #         if order.order_type == 'service' or order.order_type == 'project':
    #             for line in order.order_line:
    #                 if not line.product_id.project_template_id and line.product_id.detailed_type == 'product':
    #                     location_id = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations').id
    #                     self.env['stock.quant'].create({
    #                         'product_id': line.product_id.id,
    #                         'location_id': location_id,
    #                         'quantity': line.product_uom_qty,
    #                     })
    #     self.is_complete_saleoder = True
    #     return res

    def _compute_form_counts(self):
        for order in self:
            order.calibration_form_count = self.env['calibration.form'].search_count(
                [('saleorder_id', '=', order.id)])
            order.lsa_form_count = self.env['lsa.form'].search_count([('saleorder_id', '=', order.id)])
            order.ffa_form_count = self.env['ffa.form'].search_count([('saleorder_id', '=', order.id)])
            order.field_service_form_count = self.env['field.service'].search_count([('saleorder_id', '=', order.id)])
            order.navigation_communication_form_count = self.env['navigation.communication'].search_count(
                [('saleorder_id', '=', order.id)])

    def check_product_categories_and_create_forms(self):
        if self.forms_created:
            raise ValidationError("Job sheet is already created for this sale order.")

        if self.job_sheet_no == _('New'):
            self.job_sheet_no = f"JS_{self.name}"

        used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations', raise_if_not_found=False)
        job_note = self.env['ir.sequence'].next_by_code('job.note') or '/'

        if self.job_delivery_note == _('New'):
            self.job_delivery_note = f"DN_{used_location.name}{job_note}"

        form_counter = 1

        data_calibration = self.order_line.filtered(lambda l: l.is_jobsheet)
        if data_calibration:
            if all(li.product_template_id.categ_id.is_scope for li in data_calibration):
                self.is_not_product_calibration = False
            else:
                self.is_not_product_calibration = True

        if not any(self.order_line.filtered(lambda l: l.is_jobsheet and (
                l.product_template_id.categ_id.is_calibration or
                l.product_template_id.categ_id.is_lsa or
                l.product_template_id.categ_id.is_ffa or
                l.product_template_id.categ_id.is_navigation_communication or
                l.product_template_id.categ_id.is_field_service
        ))):
            self.is_not_product_calibration = True

        # Calibration
        for line in self.order_line.filtered(lambda l: l.is_jobsheet and l.product_template_id.categ_id.is_calibration):
            form_sequence = f"{self.name}.{str(form_counter).zfill(2)}"
            calibration_form = self.env['calibration.form'].create({
                'product_category_parent_id': line.product_id.categ_id.parent_id.id,
                'product_category_id': line.product_id.categ_id.id,
                'partner_id': self.partner_id.id,
                'saleorder_id': self.id,
                'lead_id': self.opportunity_id.id if self.opportunity_id else self.estimation_id.lead_id.id,
                'inspection_calibration_id': line.inspection_calibration_id.id,
                'job_sheet_number': self.job_sheet_no,
                'certificate_no': form_sequence,
                'name': self.job_sheet_no,
                'product_id': line.product_template_id.id,
                'qty_calibration': line.balance_qty,
                'price_unit': line.price_unit,
                'vessel_id': self.vessel_id.id,
            })
            self.calibration_id = calibration_form.id
            calibration_form._onchange_certificates_id()
            calibration_form._onchange_product_id()
            form_counter += 1

        # LSA
        for line in self.order_line.filtered(lambda l: l.is_jobsheet and l.product_template_id.categ_id.is_lsa):
            form_sequence = f"{self.name}.{str(form_counter).zfill(2)}"
            lsa_form = self.env['lsa.form'].create({
                'product_category_parent_id': line.product_id.categ_id.parent_id.id,
                'product_category_id': line.product_id.categ_id.id,
                'partner_id': self.partner_id.id,
                'saleorder_id': self.id,
                'lead_id': self.opportunity_id.id if self.opportunity_id else self.estimation_id.lead_id.id,
                'product_id': line.product_template_id.id,
                'job_sheet_number': self.job_sheet_no,
                'certificate_no': form_sequence,
                'name': self.job_sheet_no,
                'qty_lsa': line.balance_qty,
                'price_unit': line.price_unit,
                'vessel_id': self.vessel_id.id,
                'inspection_calibration_id': line.inspection_calibration_id.id,
            })
            self.lsa_id = lsa_form.id
            lsa_form._onchange_certificates_id()
            lsa_form._onchange_product_id()
            form_counter += 1

        # FFA
        for line in self.order_line.filtered(lambda l: l.is_jobsheet and l.product_template_id.categ_id.is_ffa):
            form_sequence = f"{self.name}.{str(form_counter).zfill(2)}"
            ffa_form = self.env['ffa.form'].create({
                'product_category_parent_id': line.product_id.categ_id.parent_id.id,
                'product_category_id': line.product_id.categ_id.id,
                'partner_id': self.partner_id.id,
                'saleorder_id': self.id,
                'lead_id': self.opportunity_id.id if self.opportunity_id else self.estimation_id.lead_id.id,
                'product_id': line.product_template_id.id,
                'job_sheet_number': self.job_sheet_no,
                'certificate_no': form_sequence,
                'name': self.job_sheet_no,
                'qty_ffa': line.balance_qty,
                'price_unit': line.price_unit,
                'vessel_id': self.vessel_id.id,
                'inspection_calibration_id': line.inspection_calibration_id.id,
            })
            self.ffa_id = ffa_form.id
            ffa_form._onchange_certificates_id()
            ffa_form._onchange_product_id()
            form_counter += 1

        # Navigation & Communication
        for line in self.order_line.filtered(
                lambda l: l.is_jobsheet and l.product_template_id.categ_id.is_navigation_communication):
            form_sequence = f"{self.name}.{str(form_counter).zfill(2)}"
            navigation_form = self.env['navigation.communication'].create({
                'product_category_parent_id': line.product_id.categ_id.parent_id.id,
                'product_category_id': line.product_id.categ_id.id,
                'partner_id': self.partner_id.id,
                'saleorder_id': self.id,
                'lead_id': self.opportunity_id.id if self.opportunity_id else self.estimation_id.lead_id.id,
                'product_id': line.product_template_id.id,
                'job_sheet_number': self.job_sheet_no,
                'certificate_no': form_sequence,
                'name': self.job_sheet_no,
                'qty_nav_com': line.balance_qty,
                'price_unit': line.price_unit,
                'vessel_id': self.vessel_id.id,
                'inspection_calibration_id': line.inspection_calibration_id.id,
            })
            self.navigation_id = navigation_form.id
            navigation_form._onchange_certificates_id()
            navigation_form._onchange_product_id()
            form_counter += 1

        # Field Service
        for line in self.order_line.filtered(
                lambda l: l.is_jobsheet and l.product_template_id.categ_id.is_field_service):
            form_sequence = f"{self.name}.{str(form_counter).zfill(2)}"
            field_service_form = self.env['field.service'].create({
                'product_category_parent_id': line.product_id.categ_id.parent_id.id,
                'product_category_id': line.product_id.categ_id.id,
                'partner_id': self.partner_id.id,
                'saleorder_id': self.id,
                'lead_id': self.opportunity_id.id if self.opportunity_id else self.estimation_id.lead_id.id,
                'product_id': line.product_template_id.id,
                'job_sheet_number': self.job_sheet_no,
                'certificate_no': form_sequence,
                'name': self.job_sheet_no,
                'qty_field_service': line.balance_qty,
                'price_unit': line.price_unit,
                'vessel_id': self.vessel_id.id,
                'inspection_calibration_id': line.inspection_calibration_id.id,
            })
            self.field_service_id = field_service_form.id
            field_service_form._onchange_certificates_id()
            field_service_form._onchange_product_id()
            form_counter += 1

        self.forms_created = True

    def create_smart_button_calibration(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calibration Form',
            'view_mode': 'tree,form',
            'res_model': 'calibration.form',
            'domain': [('saleorder_id', '=', self.id)],
            'context': {'create': False}
        }

    def create_smart_button_lsa(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'LSA Form',
            'view_mode': 'tree,form',
            'res_model': 'lsa.form',
            'domain': [('saleorder_id', '=', self.id)],
            'context': {'create': False}
        }

    def create_smart_button_ffa(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'FFA Form',
            'view_mode': 'tree,form',
            'res_model': 'ffa.form',
            'domain': [('saleorder_id', '=', self.id)],
            'context': {'create': False}
        }

    def create_smart_button_field_service(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'FIELD_SERVICE Form',
            'view_mode': 'tree,form',
            'res_model': 'field.service',
            'domain': [('saleorder_id', '=', self.id)],
            'context': {'create': False}
        }

    def create_smart_button_navigation_communication(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Navigation and Communication Form',
            'view_mode': 'tree,form',
            'res_model': 'navigation.communication',
            'domain': [('saleorder_id', '=', self.id)],
            'context': {'create': False}
        }

    def view_service_delivery(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Service Delivery',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('lead_id', '=',self.opportunity_id.id ),('repair_id','!=',False)],
            'context': {'create': False}
        }

    def repair_moves(self):

        # sml_ids = self.env['stock.move.line']
        # if self.calibrate_repair_ids:
        #     for repair in self.calibrate_repair_ids:
        #         sml_ids |= self.env['stock.move.line'].search([('reference', '=', repair.name)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Repair Order',
            'view_mode': 'tree,form',
            'res_model': 'repair.order',
            'domain': [('saleorder_id', '=',self.id )],
            'context': {'create': False,'search_default_filter_under_repair': 1}
        }

    # def check_product_categories_and_create_forms(self):
    #     product_categories = self.order_line.mapped('product_template_id.categ_id')
    #
    #     cat_calibration = []
    #     filtered_products = self.order_line.mapped('product_template_id').filtered(
    #         lambda l: l.categ_id.parent_id.is_calibration
    #     )
    #
    #     for rec in filtered_products:
    #         if rec.categ_id.id not in cat_calibration:
    #             cat_calibration.append(rec.categ_id.id)
    #
    #     for categ_id in cat_calibration:
    #         products_in_category_calibration = filtered_products.filtered(lambda p: p.categ_id.id == categ_id)
    #
    #         if products_in_category_calibration:
    #             category_record = self.env['product.category'].browse(categ_id)
    #             calibration_form = self.env['calibration.form'].create({
    #                 'product_category_parent_id':category_record.parent_id.id,
    #                 'product_category_id':categ_id ,
    #                 'partner_id': self.partner_id.id,
    #                 'saleorder_id': self.id,
    #                 'product_id': products_in_category_calibration
    #                 # 'equipment_records_ids': [(6, 0, products_in_category_calibration.ids)]
    #             })
    #
    #     cat_lsa = []
    #     filtered_lsa_products = self.order_line.mapped('product_template_id').filtered(
    #         lambda l: l.categ_id.parent_id.is_lsa
    #     )
    #     for rec in filtered_lsa_products:
    #         if rec.categ_id.id not in cat_lsa:
    #             cat_lsa.append(rec.categ_id.id)
    #
    #     for categ_id in cat_lsa:
    #         products_in_category = filtered_lsa_products.filtered(lambda p: p.categ_id.id == categ_id)
    #
    #         if products_in_category:
    #             category_record = self.env['product.category'].browse(categ_id)
    #             lsa_form = self.env['lsa.form'].create({
    #                 'product_category_parent_id':category_record.parent_id.id,
    #                 'product_category_id':categ_id ,
    #                 'partner_id': self.partner_id.id,
    #                 'saleorder_id': self.id,
    #                 'equipment_records_ids': [(6, 0, products_in_category.ids)]
    #             })
    #
    #     cat_ffa = []
    #     filtered_ffa_products = self.order_line.mapped('product_template_id').filtered(
    #         lambda l: l.categ_id.parent_id.is_ffa
    #     )
    #
    #     for rec in filtered_ffa_products:
    #         if rec.categ_id.id not in cat_ffa:
    #             cat_ffa.append(rec.categ_id.id)
    #
    #     for categ_id in cat_ffa:
    #         products_in_category_ffa = filtered_ffa_products.filtered(lambda p: p.categ_id.id == categ_id)
    #
    #         if products_in_category_ffa:
    #             category_record = self.env['product.category'].browse(categ_id)
    #             ffa_form = self.env['ffa.form'].create({
    #                 'product_category_parent_id': category_record.parent_id.id,
    #                 'product_category_id': categ_id,
    #                 'partner_id': self.partner_id.id,
    #                 'saleorder_id': self.id,
    #                 'equipment_records_ids': [(6, 0, products_in_category_ffa.ids)]
    #             })


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    scope = fields.Char(string="Scope", store=True)
    product_catgeory_id = fields.Many2one('product.category', string="Product Category", related="product_id.categ_id")
    is_jobsheet = fields.Boolean(default=False, copy=False)
    inspection_calibration_id = fields.Many2one('inspection.calibration', string="Inspection")

    @api.depends('product_id', 'inspection_calibration_id', 'inspection_calibration_id.lot_number_text')
    def _compute_name(self):
        super(SaleOrderLine, self)._compute_name()
        for rec in self.filtered(lambda r: r.inspection_calibration_id):
            rec.name = rec.inspection_calibration_id.lot_number_text or rec.name

    @api.onchange('product_id')
    def _onchange_product_ctg_id(self):
        for line in self:
            product_catgeory = line.product_id.categ_id
            line.product_catgeory_id = product_catgeory if product_catgeory else ''
            line.scope = product_catgeory.parent_id.name if product_catgeory.parent_id.name else ''

    # @api.constrains('product_uom_qty', 'qty_delivered')
    # def check_product_qty_qty_received(self):
    #     for record in self:
    #         if record.product_uom_qty and record.qty_delivered and record.product_uom_qty < record.qty_delivered:
    #             raise UserError(_('The quantity received cannot exceed the product quantity.'))

class KGStockMove(models.Model):
    _inherit = 'stock.move'

    repair_line_type = fields.Selection([
        ('add', 'Add'),
        ('remove', 'Remove'),
    ], 'Type', store=True, index=True)

    repair_line_type_display = fields.Selection(
        [('add', 'Add'), ('remove', 'Remove')],
        string="Type", default="add",
       readonly = False,required=True
    )

    @api.onchange('repair_line_type_display')
    def _onchange_repair_line_type_display(self):
        for record in self:
            record.repair_line_type = record.repair_line_type_display



    # @api.model
    # def _get_new_question_type(self):
    #     """Cette methode permet de mettre à jour les type de question,
    #        Dans le but de retirer les options 'multiple_choice' et 'matrix'
    #     """
    #
    # selection = [
    #     ('text_box', 'Zone de texte à plusieurs lignes'),
    #     ('char_box', 'Zone de texte sur une seule ligne'),
    #     ('numerical_box', 'Valeur numérique'),
    #     ('date', 'Date'),
    #     ('datetime', 'Date et heure'),
    #     ('simple_choice', 'Choix multiple : une seule réponse')
    # ]
    # return selection
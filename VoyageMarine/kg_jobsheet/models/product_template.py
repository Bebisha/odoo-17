from odoo import models, fields, api, _
from odoo.tools import format_datetime, formatLang

from odoo.exceptions import UserError, ValidationError


class KGProductTemplate(models.Model):
    _inherit = "product.template"

    is_equipment = fields.Boolean(string="Equipment", help="Check this box if the item is considered equipment.")
    is_master_equipment = fields.Boolean(string="IS Master Equipment",
                                         help="Check this box if this equipment serves as the master reference for other equipment.")
    certificate_id = fields.Many2one('certificate.master', string="Certificate",)
    sub_category_id = fields.Many2one("product.category", string="Subcategory", domain="[('parent_id', '=', categ_id)]",readonly=False)
    equipment_make = fields.Char(string='Make')
    equipment_serial_no = fields.Char(string='Serial Number')
    equipment_certificate_no = fields.Char(string='Certificate Number')
    equipment_traceability = fields.Char(string='Traceability')

    category_ids = fields.Many2many('product.category', string='Categories' )
    standard_used_id  = fields.Many2one('standard.used',string="Standard Used")
    work_instruction_id  = fields.Many2one('work.instruction',string="Work Instruction")


    @api.constrains('default_code')
    def _check_default_code_required(self):
        for rec in self:
            if not rec.default_code and not rec.is_equipment:
                raise ValidationError("Internal Reference is required for all products.")

    @api.onchange('product_group_id')
    def onchange_product_group_id(self):
        if self.product_group_id:
            categories = self.env['product.category'].search([('product_group_id', '=', self.product_group_id.id),('parent_id', '=', False)])
            self.category_ids = categories
        else :
            self.category_ids = []
            self.categ_id = ''

    @api.onchange('certificate_id')
    def onchange_certificate_id(self):
        if self.certificate_id:
            certificate = self.env['certificate.master'].search(
                [('id', '=', self.certificate_id.id)])

            self.standard_used_id = certificate.standard_used_id.id
            self.work_instruction_id = certificate.work_instruction.id
        else:
            self.standard_used_id = ''
            self.work_instruction_id = ''

    # @api.model
    # def create(self, vals):
    #     calibration_group = self.env['product.group'].search(
    #         [('name', '=', 'Calibration')], limit=1
    #     )
    #
    #     if vals.get('is_equipment'):
    #         if calibration_group:
    #             vals['product_group_id'] = calibration_group.id
    #     else:
    #         # Validation: Non-equipment cannot be Calibration
    #         if vals.get('product_group_id') == calibration_group.id:
    #             raise ValidationError(
    #                 _("Only Equipment products can have Product Group as Calibration.")
    #             )
    #
    #     return super().create(vals)
    #
    # def write(self, vals):
    #     calibration_group = self.env['product.group'].search(
    #         [('name', '=', 'Calibration')], limit=1
    #     )
    #
    #     for rec in self:
    #         is_equipment = vals.get('is_equipment', rec.is_equipment)
    #         product_group_id = vals.get(
    #             'product_group_id', rec.product_group_id.id
    #         )
    #
    #         if is_equipment:
    #             if calibration_group:
    #                 vals['product_group_id'] = calibration_group.id
    #         else:
    #             # Validation: Non-equipment cannot be Calibration
    #             if product_group_id == calibration_group.id:
    #                 raise ValidationError(
    #                     _("Only Equipment products can have Product Group as Calibration.")
    #                 )
    #
    #     return super().write(vals)

class KGProductProduct(models.Model):
    _inherit = "product.product"


    @api.onchange('product_group_id')
    def onchange_products_group_id(self):
        if self.product_group_id:
            categories = self.env['product.category'].search([('product_group_id', '=', self.product_group_id.id),('parent_id', '=', False)])
            self.category_ids = categories
        else :
            self.category_ids = []
            self.categ_id = ''

    @api.onchange('certificate_id')
    def onchange_certificate_id(self):
        if self.certificate_id:
            certificate = self.env['certificate.master'].search(
                [('id', '=', self.certificate_id.id)])

            self.standard_used_id = certificate.standard_used_id.id
            self.work_instruction_id = certificate.work_instruction.id
        else:
            self.standard_used_id = ''
            self.work_instruction_id = ''

    @api.model
    def create(self, vals):
        calibration_group = self.env['product.group'].search(
            [('name', '=', 'Calibration')], limit=1
        )

        if vals.get('is_equipment'):
            if calibration_group:
                vals['product_group_id'] = calibration_group.id
        else:
            # Validation: Non-equipment cannot be Calibration
            if vals.get('product_group_id') == calibration_group.id:
                raise ValidationError(
                    _("Only Equipment products can have Product Group as Calibration.")
                )

        return super().create(vals)

    def write(self, vals):
        calibration_group = self.env['product.group'].search(
            [('name', '=', 'Calibration')], limit=1
        )

        for rec in self:
            is_equipment = vals.get('is_equipment', rec.is_equipment)
            product_group_id = vals.get(
                'product_group_id', rec.product_group_id.id
            )

            if is_equipment:
                if calibration_group:
                    vals['product_group_id'] = calibration_group.id
            else:
                # Validation: Non-equipment cannot be Calibration
                if product_group_id == calibration_group.id:
                    raise ValidationError(
                        _("Only Equipment products can have Product Group as Calibration.")
                    )

        return super().write(vals)




    # @api.onchange('categ_id')
    # def categ_id

    # @api.onchange('categ_id')
    # def _onchnage_is_gas_detection(self):
    #     for product in self:
    #         if product.categ_id.is_gas_detection == True:
    #             product.is_gas_detection = True
    #         if product.categ_id.is_fire_detection == True:
    #             product.is_fire_detection = True
    #         if product.categ_id.is_electrical == True:
    #             product.is_electrical = True
    #         if product.categ_id.is_measuring_control == True:
    #             product.is_measuring_control = True
    #         if product.categ_id.is_navigation == True:
    #             product.is_navigation = True
    #         if product.categ_id.is_communication == True:
    #             product.is_communication = True
    #         if product.categ_id.is_featured_marine == True:
    #             product.is_featured_marine = True
    #         if product.categ_id.is_cables == True:
    #             product.is_cables = True
    #         if product.categ_id.is_hardwares == True:
    #             product.is_hardwares = True
    #         if product.categ_id.is_tools == True:
    #             product.is_tools = True
    #         if product.categ_id.is_consumables == True:
    #             product.is_consumables = True
    #         if product.categ_id.is_health_safety == True:
    #             product.is_health_safety = True

    @api.onchange('product_group_id')
    def onchnage_products_group_id(self):
        ids = self.env['product.group'].search([('code', '=', 'CAL')])
        if self.product_group_id == ids :
            print("lllllllllll")
            return {'domain': {
                'categ_id': [('is_scope','=',True)]}}
        else:
            self.categ_id = ''


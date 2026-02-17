
from odoo import models, fields,api,_

class CertificateMaster(models.Model):
    _name = 'certificate.master'
    _description = 'Certificate Master'
    _rec_name = 'display_name'

    @api.depends('name', 'product_category_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.product_category_id:
                rec.display_name = f"{rec.name}({rec.product_category_id.name})({rec.child_category_id.name})"

    display_name = fields.Char(compute='_compute_display_name')
    name = fields.Char(string="Certificate No"  )
    equipment_id = fields.Many2one('equipment.master', string="Equipment"  , domain="[('id', 'in', equipment_records_ids)]")
    equipment_category_id = fields.Many2one('equipment.category', string="Equipment Category")
    product_category_id = fields.Many2one('product.category', string="Scope")
    child_category_id = fields.Many2one(
        'product.category',
        string="Product Category",
        domain="[('parent_id', '=', product_category_id)]"
    )
    product_category = fields.Many2one('product.category', string="Equipment Category")
    product_id = fields.Many2one('product.template', string="Equipment", domain="[('categ_id', '=', child_category_id)]" )
    certificate =fields.Html(string='Certificate')
    equipment_records_ids = fields.Many2many('product.template')
    standard_used_id = fields.Many2one('standard.used', string="Standard Used ")
    work_instruction = fields.Many2one('work.instruction', string="Work Instruction",
                                      )

    note = fields.Char(string='Note')
    description = fields.Html(string='Terms and Conditions')
    active = fields.Boolean(string="Active", default=True)


    # @api.onchange('product_category_id')
    # def _onchange_product_category_id_certificate(self):
    #     if self.product_category_id:
    #         equipment_category_id = self.product_category_id.id
    #         equipment_category = self.product_category_id.parent_id
    #
    #         equipment_records = self.env['product.template'].search(
    #             [('categ_id', '=', equipment_category_id)])
    #
    #         self.equipment_records_ids = [(6, 0, equipment_records.ids)]
    #         self.product_category = equipment_category
    #

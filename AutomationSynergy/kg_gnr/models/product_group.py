from odoo import models, fields, api


class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'Group Master'

    name = fields.Char(required=True, string='Name')


class ProductSubGroup(models.Model):
    _name = 'product.sub.group'

    _description = 'Sub Group Master'

    name = fields.Char(required=True, string='Name')
    group_id = fields.Many2one('product.group', string='Group', )

    def create(self, values):
        # Call the original create method
        record = super(ProductSubGroup, self).create(values)

        pro = self.env['product.template'].sudo().search([('sub_group_id', '=', record.id)])

        return record


class ProductInh(models.Model):
    _inherit = 'product.template'
    _description = 'Include group Field'

    group_id = fields.Many2one('product.group')
    sub_group_id = fields.Many2one('product.sub.group', domain="[('group_id', '=', group_id)]")

    def write(self, values):
        """to get newly created subgroup under the group"""
        result = super(ProductInh, self).write(values)
        subgroup_id = values.get('sub_group_id')
        sub_gr_pro = self.env['product.sub.group'].sudo().browse([subgroup_id])
        if self.group_id:
            if not sub_gr_pro.group_id:
                sub_gr_pro.group_id = self.group_id
        return result

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', 'Brand')
    serial = fields.Char('Serial No.')
    model_id = fields.Many2one('product.model', 'Model')
    rating_size = fields.Char('Rating/size')
    order_code = fields.Char('Order Code')
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')],
        string="Tracking", required=True, default='lot',
        compute='_compute_tracking', store=True, readonly=False, precompute=True,
        help="Ensure the traceability of a storable product in your warehouse.")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        args = list(args or [])
        if name:
            args += ['|', '|', '|', '|', '|', '|', ('name', operator, name), ('default_code', operator, name),
                     ('serial', operator, name),
                     ('brand_id', operator, name), ('model_id', operator, name), ('rating_size', operator, name),
                     ('order_code', operator, name)
                     ]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # brand_id = fields.Many2one('product.brand', 'Brand')
    # serial = fields.Char('Serial No.')
    # model_id = fields.Many2one('product.model', 'Model', required=True)
    # rating_size = fields.Char('Rating/size', required=True)
    # order_code = fields.Char('Order Code', required=True)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        args = list(args or [])
        if name:
            args += ['|', '|', '|', '|', '|', '|', ('name', operator, name), ('default_code', operator, name),
                     ('serial', operator, name),
                     ('brand_id', operator, name), ('model_id', operator, name), ('rating_size', operator, name),
                     ('order_code', operator, name)
                     ]
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)

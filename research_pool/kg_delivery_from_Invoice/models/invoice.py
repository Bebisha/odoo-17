from odoo import api, models, fields


class KgAccountMove(models.Model):
    _inherit = 'account.move'

    picking_ids = fields.One2many('stock.picking', 'invoice_id', string='Delivery Orders')
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string="Picking type",
        domain=[('code', '=', 'outgoing')],
        default=lambda self: self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
    )
    delivery_button_visible = fields.Boolean(default=False, string="Appointment Button Visible")

    def stock(self):
        return {
            'name': 'Delivery Order',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            # 'context': {},
            'domain': [('invoice_id', '=', self.id)],
            'target': 'current',

        }


    def action_post(self):
        print('llllllllllllllll')

        move_line_vals = []

        for line in self.invoice_line_ids:
            print(line.product_id.id, 'llllllllllllll')
            location_id = line.product_id.property_stock_inventory.id
            move_line_vals.append((0, 0, {
                                'product_id': line.product_id.id,
                                'description_picking': line.product_id.name,
                                'name': line.name,
                                'product_uom_qty': line.quantity,
                                'product_uom': line.product_id.uom_id.id,
                                'location_id':location_id,
                                'location_dest_id': self.partner_id.property_stock_customer.id,
                            }))

        picking_vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': self.picking_type_id.id,
            'origin': self.name,
            'location_dest_id': self.partner_id.property_stock_customer.id,
            'move_ids_without_package': move_line_vals,
            'move_type': 'outgoing',
        }
        print('picking_vals',picking_vals)

        picking = self.env['stock.picking'].create(picking_vals)
        self.picking_ids = [(4, picking.id)]

        self.delivery_button_visible = True
        return super(KgAccountMove, self).action_post()




class KGStockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_id = fields.Many2one('account.move', string="Invoice")
    move_type = fields.Char("Move type")



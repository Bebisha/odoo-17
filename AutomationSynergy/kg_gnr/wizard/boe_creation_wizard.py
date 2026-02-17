from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BoeWizard(models.TransientModel):
    """ adding bill of entry values through wizard in multiple Purchase orders"""
    _name = 'boe.wizard'
    _description = 'Boe Creation in List'

    boe_type = fields.Selection(
        [('internal', 'Internal Transfer'),
         ('import', 'Import'),
         ], string="Bill Of Entry Type", required=1)

    boe_no = fields.Char('Bill Of Entry NO', requierd=1)
    ship_no = fields.Char('Shipping Doc NO', required=1)
    purchase_ids = fields.Many2many('purchase.order')
    sale_ids = fields.Many2many('sale.order')
    stock_ids = fields.Many2many('stock.picking')

    def add_values(self):
        for order in self:
            # if order.purchase_ids:
            #     """"create BOE from purchase"""
            #     order.purchase_ids.write({'boe_type': order.boe_type,
            #                               'boe_no': order.boe_no,
            #                               'ship_no': order.ship_no,
            #
            #                               })
            #     for rec in order.purchase_ids:
            #         if rec.picking_ids:
            #             rec.picking_ids.write({'po_boe_type': order.boe_type,
            #                                    'po_boe_no': order.boe_no,
            #                                    'po_ship_no': order.ship_no,
            #
            #                                    })
            # if order.sale_ids:
            #     """"create BOE from sales"""
            #     order.sale_ids.write({'so_boe_type': order.boe_type,
            #                           'so_boe_no': order.boe_no,
            #                           'so_ship_no': order.ship_no,
            #
            #                           })
            #     for rec in order.sale_ids:
            #         if rec.picking_ids:
            #             rec.picking_ids.write({'so_boe_type': order.boe_type,
            #                                    'so_boe_no': order.boe_no,
            #                                    'so_ship_no': order.ship_no,
            #
            #                                    })
            if order.stock_ids:
                """"create BOE from stock"""
                for rec in order.stock_ids:

                    if rec.picking_type_code == 'incoming':
                        if rec.po_boe_no:
                            raise ValidationError('Already a bill No is there!!')
                        rec.write({'po_boe_type': order.boe_type,
                                   'po_boe_no': order.boe_no,
                                   'po_ship_no': order.ship_no, })
                        # if rec.purchase_id:
                        #     rec.purchase_id.write({'boe_type': order.boe_type,
                        #                            'boe_no': order.boe_no,
                        #                            'ship_no': order.ship_no, })
                    if rec.picking_type_code == 'outgoing':
                        if rec.so_boe_no:
                            raise ValidationError('Already a bill No is there!!')
                        rec.write({'so_boe_type': order.boe_type,
                                   'so_boe_no': order.boe_no,
                                   'so_ship_no': order.ship_no, })
                        # if rec.sale_id:
                        #     rec.sale_id.write({'so_boe_type': order.boe_type,
                        #                        'so_boe_no': order.boe_no,
                        #                        'so_ship_no': order.ship_no, })

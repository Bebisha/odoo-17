from odoo import models, fields, api


class BoeReport(models.Model):
    _name = 'boe.report'
    _description = 'BOE Report'

    date_in = fields.Date('Date In')
    boe_type_in = fields.Selection(
        [('internal', 'Internal Transfer'),
         ('import', 'Import'),
         ], string="Bill Of Entry Type IN")
    doc_no = fields.Char('Doc No In')
    partner_id = fields.Many2many('res.partner', 'Exporter')
    partner = fields.Char('Exporter')
    boe_ref = fields.Char('Boe NO IN')
    product_id = fields.Many2one('product.template',string='Description')
    hs_code = fields.Char('HS CODE')
    coo_code = fields.Char('COO')
    weight = fields.Float('Weight')
    package = fields.Float('Package')
    qty_actual = fields.Float('QTY')

    group_id = fields.Many2one('product.group', string='Group')

    date_out = fields.Date('Date OUT')
    doc_no_out = fields.Char('Doc No OUT')
    customer_id = fields.Many2many('res.partner', 'Importer')
    customer = fields.Char('Importer')
    boe_ref_out = fields.Char('Boe NO OUT')
    hs_code_out = fields.Char('HS CODE')
    coo_code_out = fields.Char('COO', )
    boe_type_out = fields.Selection(
        [('internal', 'Internal Transfer'),
         ('import', 'Import'),
         ], string="Bill Of Entry Type OUT")
    weight_out = fields.Float('Weight')
    package_out = fields.Float('Package')
    qty_actual_out = fields.Float('QTY')
    group_out_id = fields.Many2one('product.group', string='description')
    remaining_quantity = fields.Float('Remaining Quantity')

    def load_boe_records(self):
        """adding the values to the tree view"""
        rec = self.env['stock.lot'].search([])
        domain_list = []
        for data in rec:
            if data.delivery_ids:
                for line in data.picking_id.move_line_ids.filtered(
                        lambda x: x.product_id == data.product_id and x.lot_id.id == data.id):

                    remaining = line.quantity
                    for j in data.delivery_ids:
                        if j.state == 'done':
                            for vals in j.move_line_ids.filtered(
                                    lambda x: x.product_id == data.product_id and x.lot_id.id == data.id):
                                remaining = remaining - vals.quantity

                                delivery = self.create({'date_in': data.picking_id.scheduled_date,
                                                        'doc_no_out': data.picking_id.po_ship_no,
                                                        'boe_type_in': data.picking_id.po_boe_type,
                                                        'partner': data.picking_id.partner_id.name,
                                                        'boe_ref': data.picking_id.po_boe_no,
                                                        'qty_actual': line.quantity,
                                                        'hs_code': line.hs_code,
                                                        'coo_code': line.coo_code,
                                                        'hs_code_out': j.hs_code_out,
                                                        'coo_code_out': j.coo_code_out,
                                                        'group_id': line.product_id.group_id.id,
                                                        'product_id': line.product_id.product_tmpl_id.id,
                                                        'date_out': j.scheduled_date,
                                                        'doc_no': j.so_ship_no,
                                                        'customer': j.partner_id.name,
                                                        'boe_ref_out': j.so_boe_no,
                                                        'boe_type_out': j.so_boe_type,
                                                        'qty_actual_out': vals.quantity,
                                                        'group_out_id': vals.product_id.group_id.id,
                                                        'remaining_quantity': remaining,

                                                        }
                                                       )

                                domain_list.append(delivery.id)
            elif data.picking_id:
                return_1 = 0
                if data.picking_id.return_ids:
                    for ret in data.picking_id.return_ids.move_line_ids.filtered(
                            lambda x: x.product_id == data.product_id and x.lot_id.id == data.id):
                        return_1 = ret.quantity
                else:
                    return_1 = 0

                for line in data.picking_id.move_line_ids.filtered(
                        lambda x: x.product_id == data.product_id and x.lot_id.id == data.id):
                    if line.picking_id.state == 'done':
                        print(line.picking_id,"line.picking_id")
                        print(line.hs_code,"line.hs_code")
                        print(line.coo_code,"line.coo_code")
                        remaining = line.quantity
                        pickin = self.create({'date_in': data.picking_id.scheduled_date,
                                              'doc_no': data.picking_id.po_ship_no,
                                              'boe_type_in': data.picking_id.po_boe_type,
                                              'hs_code': line.hs_code,
                                              'coo_code': line.coo_code,
                                              'hs_code_out':line.hs_code_out,
                                              'coo_code_out':line.coo_code_out,
                                              'product_id': line.product_id.product_tmpl_id.id,

                                              'partner': data.picking_id.partner_id.name,
                                              'boe_ref': data.picking_id.po_boe_no,
                                              'qty_actual': line.quantity - return_1,

                                              'group_id': line.product_id.group_id.id,
                                              'remaining_quantity': remaining

                                              }
                                             )
                        print(pickin.hs_code,'jjjjhhhhhhhhhhhh')
                        print(pickin.coo_code,'hggggggggggggggggg')
                        domain_list.append(pickin.id)

        return {
            'name': 'BOE Report',
            'view_mode': 'tree',
            'domain': [('id', 'in', domain_list)],
            'res_model': 'boe.report',
            'type': 'ir.actions.act_window',
            'context': {
                'search_default_boe_no_in': 1,
                # 'group_by': 'boe_ref',
            },
            'target': 'main'
        }

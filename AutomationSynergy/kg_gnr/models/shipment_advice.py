# -*- coding: utf-8 -*-

from odoo import models, fields, _, api, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_round, float_is_zero, groupby
from datetime import date, datetime
import time


class ShipmentAdvice(models.Model):
    _name = 'shipment.advice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Shipment Advice'
    _rec_name = 'name'
    _order = 'name desc, id desc'

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        p_type = self.picking_type_id
        if not (p_type and p_type.code == 'incoming' and (
                p_type.warehouse_id.company_id == self.company_id or not p_type.warehouse_id)):
            self.picking_type_id = self._get_picking_type(self.company_id.id)

    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return picking_type[:1]

    name = fields.Char(string='RReferencer', required=True, readonly=True, default=lambda self: _('New'), copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', 'Responsible', copy=False, default=lambda self: self.env.user, required=True,
                              tracking=True)
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('done', 'Closed'),
            ('boe', "BOE"),
            ('cancel', 'Cancelled'),
        ],
        required=True, tracking=True, default='draft')
    shipment_no = fields.Char('Shipment No.', copy=False, tracking=True)
    container_no = fields.Char('Container No.', copy=False, tracking=True)
    container_title = fields.Char('Container Title.', copy=False, tracking=True)
    bill_no = fields.Char('BL No.', copy=False, tracking=True)
    departure_date = fields.Date('Departure Date', tracking=True)
    arrival_date = fields.Date('Arrival Date', tracking=True)
    expected_date = fields.Date('Expected Date', tracking=True)
    notes = fields.Text('Notes')
    shipment_lines = fields.One2many(comodel_name='shipment.advice.line', inverse_name='shipment_id',
                                     string='Shipment Products', required=False, tracking=True)
    shipment_summary_lines = fields.One2many(comodel_name='shipment.advice.summary', inverse_name='shipment_id',

                                             string='Shipment Summary', required=False, tracking=True)
    vendor_id = fields.Many2one('res.partner')
    # goodsin_id = fields.Many2one('goodsin.transit')
    next_id = fields.Integer()
    is_inspected = fields.Boolean(string="Is inspected", default=False)
    invoice_status = fields.Boolean(default=False)
    bill_of_entry_id = fields.Many2one('bill.of.entry', string="Bill of Entry")
    is_boe = fields.Boolean(string="BOE", copy=False)
    container_load = fields.Selection([('LCL', 'LCL'), ('FCL', 'FCL')], default='FCL')
    is_update_qty = fields.Boolean(string="Is Update Qty", default=False, copy=False)
    is_costsheet = fields.Boolean(string="Is Cost Sheet", default=False, copy=False)
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To',
                                      required=True, default=_default_picking_type,
                                      domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
                                      help="This will determine operation type of incoming shipment")

    is_done_cost_sheet = fields.Boolean(default=False, copy=False)

    def action_create_cost_sheet(self):
        cost_sheet = self.env['po.cost.sheet'].create({
            'boe_no': self.bill_of_entry_id.id,
            'git_ids': [self.id],
        })
        cost_sheet._onchange_git()
        action = self.env.ref("kg_oki_purchase.po_cost_sheet_menu_action").sudo().read()[0]
        action["views"] = [(self.env.ref("kg_oki_purchase.po_cost_sheet_form").id, "form")]
        action["res_id"] = cost_sheet.id
        self.is_costsheet = True
        return action

    def view_costsheet(self):
        action = self.env.ref("kg_oki_purchase.po_cost_sheet_menu_action").sudo().read()[0]
        action["views"] = [(self.env.ref("kg_oki_purchase.po_cost_sheet_form").id, "form")]
        cs = self.env['po.cost.sheet'].search([('git_ids', '=', self.id)])
        action["res_id"] = cs.id
        return action

    def action_update_qty(self):
        shipment_line = []
        active_id = self.env['shipment.advice'].browse(self.id)
        if active_id:
            for line in active_id.shipment_summary_lines:
                line_vals = (0, 0, {
                    'product_id': line.product_id.id,
                    'shortage_qty': line.scrapped_package_qty,
                    'shipping_qty': line.shipped_packaging_qty,
                    'shipment_advice_summary_id': line.id
                })
                shipment_line.append(line_vals)

        action = {
            'name': 'Update Quantity',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'kg.update.qty.wizard',
            'target': 'new',
            'context': {
                'default_shipment_id': self.id,
                'default_line_ids': shipment_line,
            }
        }
        return action

    def autopopulate_purchase_line(self):
        return {
            'res_model': 'po.autopopulate.order.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref("kg_gnr.po_autopopulate_orderline_wizard").id,
            'target': 'new'
        }

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '[%s] %s' % (rec.bill_no, rec.name)))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('bill_no', operator, name)]
        return self._search(domain + args, limit=limit, order=None)

    @api.constrains('attachment_ids')
    def _check_attachment_ids(self):
        if not self:
            return
        if len(self.attachment_ids.ids) < 6:
            raise ValidationError('Some Attachments are missing.')
        for attach in self.attachment_ids:
            if not attach.doc_attachment_partner and not attach.override_doc:
                raise ValidationError(_('Attachments missing for %s') % attach.document_name)

    # @api.model
    # def create(self, vals):
    #     if not vals.get('name') or vals['name'] == _('New'):
    #         vendor = self.env['res.partner'].search([('id', '=', vals.get('vendor_id'))]).name
    #         # vendor_code = vendor[0:3]
    #         ir_record = self.env['shipment.advice'].search([], limit=1, order="id desc")
    #         seq = self.env['ir.sequence']
    #         # if len(ir_record):
    #         #     if ir_record.next_id != 0:
    #         #         seq = ir_record.next_id+1
    #         #     else:
    #         #         seq = 1
    #         # else:
    #         #     seq = 1
    #         year = str(date.today().year)
    #         l = len(year)
    #         yr = year[l - 2:]
    #         sequence = "SH-" + str(yr) + str(seq.next_by_code('shipment.advice'))
    #         vals['name'] = sequence or _('New')
    #         vals['next_id'] = seq
    #     return super(ShipmentAdvice, self).create(vals)
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('goodsin.sequence') or 'New'
        return super(ShipmentAdvice, self).create(vals)

    def _create_summary(self):
        product_ids = self.shipment_lines.mapped('product_id')
        shipment_lines = self.shipment_lines
        summary_lines = []
        for product in product_ids:
            lines = shipment_lines.filtered(lambda l: l.product_id.id == product.id)
            packaging_id = lines.mapped('product_packaging_id')
            values = {
                'product_id': product.id,
                'product_packaging_id': packaging_id[0].id if packaging_id else False,
                'shipped_packaging_qty': sum(lines.mapped('shipped_packaging_qty')),
                'received_packaging_qty': sum(lines.mapped('shipped_packaging_qty')),
                'scrapped_package_qty': 0.0,
            }
            summary_lines.append((0, 0, values))
        self.write({
            'shipment_summary_lines': summary_lines
        })
        for vals in self.shipment_summary_lines:
            lot_line = []
            data = {
                'product_id': vals.product_id,
                'qty_done': vals.received_packaging_qty,
                'remaining_qty': vals.received_packaging_qty,
            }
            lot_line.append((0, 0, data))


    @api.ondelete(at_uninstall=False)
    def _unlink_if_not_draft(self):
        for advise in self:
            if advise.state == 'done' or advise.state == 'open':
                raise UserError(_('You can only delete draft shipment advise.'))

    def action_confirm(self):
        for rec in self:
            rec.shipment_lines.is_goods_in_transit_open = True
            purchases = self.search([('state', 'in', ('draft', 'open')), ('id', '!=', self.id)]).mapped(
                'shipment_lines.purchase_line_id').ids
            for line in self.shipment_lines:
                shiped_tot = 0.00
                shipment_line = self.env['shipment.advice.line'].search(
                    [('purchase_id', '=', line.purchase_id.id), ('product_id', '=', line.product_id.id),
                     ('shipment_id.state', 'in', ('open', 'done'))])
                for el in shipment_line:
                    shiped_tot += el.shipped_packaging_qty
                if line.shipped_packaging_qty < 0.0:
                    raise UserError(
                        _("Shipped quantity should be greater than zero.\nShipment advice: %s\nProduct: %s") % (
                            rec.name, line.product_id.name))
                if line.open_packaging_qty <= 0.0:
                    raise UserError(
                        _("Shipped quantity should be greater than zero.\nShipment advice: %s\nProduct: %s") % (
                            rec.name, line.product_id.name))
                if line.shipped_packaging_qty > line.open_packaging_qty:
                    raise UserError(
                        _("Shipped quantity should not be exceed open qty.\nShipment advice: %s\nProduct: %s") % (
                            rec.name, line.product_id.name))

                if line.product_id.id != line.purchase_line_id.product_id.id:
                    raise UserError(
                        _("Product %s should belong to the same purchase order line of %s.") % (
                            line.product_id.name, line.purchase_id.name))
                if line.purchase_line_id:
                    line.purchase_line_id.is_complete_git = True

            rec._create_summary()

            rec.write({
                'state': 'open',
            })

    def action_create_boe(self):
        self.action_done()
        # if any(line.received_packaging_qty <= 0.0 for line in self.shipment_summary_lines):
        #     raise UserError(_("Received qty in shipment summary should be greater than zero."))
        # # the below commented portion is creating  boe
        # # self.state = 'boe'
        # today = date.today()
        # # boe = self.env['bill.of.entry'].create({
        # #     'name': self.bill_no,
        # #     'partner_id': self.vendor_id.id,
        # #     'boe_expiry': self.expected_date,
        # #     'be_date': self.departure_date if self.departure_date else today,
        # #     'do_date': self.arrival_date if self.arrival_date else today,
        # #     'shipment_advice_id': self.id,
        # #     'origin_country_id': self.vendor_id.country_id,
        # #     'po_number': self.shipment_no,
        # #     'boe_value': 0,
        # #     'do_number': self.container_no,
        # # })
        # # self.is_boe = Truez
        # # self.bill_of_entry_id = boe
        # # self.state = 'boe'
        # action = self.env.ref("kg_oki_purchase.action_bill_of_entry_tree").sudo().read()[0]
        # action["context"] = {'default_partner_id':self.vendor_id.id,'default_boe_expiry':self.expected_date,'default_be_date':self.departure_date if self.departure_date else today,
        #                      'default_do_date':self.arrival_date if self.arrival_date else today,'default_origin_country_id': self.vendor_id.country_id.id,'default_po_number':self.shipment_no,
        # 'default_boe_value':0,'default_do_number':self.container_no,'default_shipment_advice_id':self.id}
        # action["views"] = [(self.env.ref("kg_oki_purchase.bill_of_entry_form_view").id, "form")]
        # return action

    def view_boe(self):
        action = self.env.ref("kg_oki_purchase.action_bill_of_entry_tree").sudo().read()[0]
        # remove default filters
        action["context"] = {}
        pickings = self.env['bill.of.entry'].search([('shipment_advice_id', '=', self.id)])
        # pickings = self.shipment_lines.mapped("purchase_id.picking_ids")
        if len(pickings) > 1:
            action["domain"] = [("id", "in", pickings.ids)]
        elif pickings:
            action["views"] = [(self.env.ref("kg_oki_purchase.bill_of_entry_form_view").id, "form")]
            action["res_id"] = pickings.id
        else:
            return False
        return action

        # ctx = {
        #     'default_partner_id': self.vendor_id.id,
        #     'default_shipment_advice_id': self.id,
        # }
        # return {
        #     'name': 'Bill of Entry',
        #     'res_model': 'bill.of.entry',
        #     'type': 'ir.actions.act_window',
        #     'context': ctx,
        #     'domain': [('shipment_advice_id', '=', self.id)],
        #     'view_type': 'form',
        #     'view_mode': 'form,list',
        #     'target': 'main'}

    def action_done(self):
        print("lllllllllllllll")
        for rec in self:
            if self.shipment_summary_lines == False:
                raise ValidationError(_("Kindly Add shipment summary lines to continue"))
            if any(line.received_packaging_qty < 0.0 for line in rec.shipment_summary_lines):
                raise UserError(_("Received qty in shipment summary should be greater than zero."))
            # if any(line.inspected_packaging_qty <= 0.0 for line in rec.shipment_lines):
            #     raise UserError(_("Inspected qty should be greater than zero."))
            for line in self.shipment_summary_lines:
                shipment_lines = self.shipment_lines.filtered(lambda l: l.product_id.id == line.product_id.id)
                qty = line.received_packaging_qty / len(shipment_lines)
                shipment_lines.write({
                    'received_packaging_qty': qty
                })
            rec.create_receipt()
            pickings = self.shipment_lines.mapped("purchase_id.picking_ids")


            rec.write({
                'state': 'done',
                'invoice_status': True,
            })

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        if self.shipment_lines:
            common_line = self.shipment_lines[0]
            move_type = 'in_invoice'
            journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
            if not journal:
                raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (
                    self.company_id.name, self.company_id.id))

            partner_invoice_id = common_line.purchase_id.partner_id.address_get(['invoice'])['invoice']
            discount_rate = 0
            for line in self.shipment_lines:
                if line.purchase_id.discount_rate != 0:
                    discount_rate = line.purchase_id.discount_rate
                    discount_type = line.purchase_id.discount_type
            if discount_rate != 0:
                invoice_vals = {
                    'ref': common_line.purchase_id.partner_ref or '',
                    'move_type': move_type,
                    'narration': self.notes,
                    'currency_id': self.company_id.currency_id.id,
                    'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
                    'partner_id': partner_invoice_id,
                    # 'fiscal_position_id': (
                    #         common_line.purchase_id or common_line.purchase_id.fiscal_position_id.get_fiscal_position(
                    #     partner_invoice_id)).id,
                    'payment_reference': common_line.purchase_id.partner_ref or '',
                    'partner_bank_id': common_line.purchase_id.partner_id.bank_ids[:1].id,
                    'invoice_origin': self.name,
                    'invoice_payment_term_id': common_line.purchase_id.payment_term_id.id,
                    'invoice_line_ids': [],
                    'company_id': self.company_id.id,
                    'discount_rate': discount_rate,
                    'discount_type': discount_type,
                }
            else:
                invoice_vals = {
                    'ref': common_line.purchase_id.partner_ref or '',
                    'move_type': move_type,
                    'narration': self.notes,
                    'currency_id': self.company_id.currency_id.id,
                    'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
                    'partner_id': partner_invoice_id,
                    # 'fiscal_position_id': (
                    #         common_line.purchase_id or common_line.purchase_id.fiscal_position_id.get_fiscal_position(
                    #     partner_invoice_id)).id,
                    'payment_reference': common_line.purchase_id.partner_ref or '',
                    'partner_bank_id': common_line.purchase_id.partner_id.bank_ids[:1].id,
                    'invoice_origin': self.name,
                    'invoice_payment_term_id': common_line.purchase_id.payment_term_id.id,
                    'invoice_line_ids': [],
                    'company_id': self.company_id.id,
                }
            return invoice_vals

    def action_create_invoice(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        self.invoice_status = False

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        for rec in self:
            rec = rec.with_company(rec.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = rec._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in rec.shipment_lines:
                packaging_uom = line.product_packaging_id.product_uom_id
                qty_per_packaging = line.product_packaging_id.qty
                qty_to_invoice = packaging_uom._compute_quantity(line.received_packaging_qty,
                                                                 line.purchase_line_id.product_uom)
                product_uom_qty, product_uom = line.purchase_line_id.product_uom._adjust_uom_quantities(qty_to_invoice,
                                                                                                        line.product_id.uom_id)
                if not float_is_zero(product_uom_qty, precision_digits=precision):
                    invoice_vals['invoice_line_ids'].append(
                        (0, 0, line._prepare_account_move_line(qty_to_invoice=product_uom_qty)))
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(
                _('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (
                x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list
        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(
            lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()
        # moves.action_post()
        return self.action_view_invoice(moves)

    def action_view_invoice(self, invoices):
        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = invoices.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result

    def action_cancel(self):
        for rec in self:
            if rec.state == 'cancel':
                pass
            # if rec.state not in ('draft', 'open'):
            #     raise UserError(_("You cannot cancel the shipment advice %s as it is already proceeded.") % rec.name)
            pickings = rec.shipment_lines.mapped('purchase_id.picking_ids')
            pick = pickings.search([('shipment_id', '=', self.id)])
            for pi in pick:
                pi.action_cancel()
                # inv = self.env['account.move'].search([('picking_id', '=', pi.id)])
                # inv.button_cancel()
            rec.shipment_summary_lines.unlink()
            rec.shipment_lines.write({
                'received_packaging_qty': 0.0
            })
            rec.write({
                'state': 'cancel',
            })
            rec.is_update_qty = False
            rec.is_boe = False

    def action_reset(self):
        for rec in self:
            if rec.state == 'draft':
                pass
            pickings = rec.shipment_lines.mapped('purchase_id.picking_ids')
            pick = pickings.search([('shipment_id', '=', self.id)])
            for pi in pick:
                pi.action_cancel()
                pi.unlink()
            # for pur in purchase:
            #     pur.shipment_id.F
                # inv = self.env['account.move'].search([('picking_id', '=', pi.id)])
                # inv.button_cancel()
            rec.shipment_summary_lines.unlink()
            rec.shipment_lines.write({
                'received_packaging_qty': 0.0
            })
            rec.write({
                'state': 'draft',
            })
            rec.is_update_qty = False
            rec.is_boe = False

    def create_receipt(self):
        results = []
        for rec in self.shipment_lines:

            print(f"Shipment Line: {rec}")
            if rec.purchase_id:
                rec.purchase_id.is_git = True
                rec.purchase_id.shipment_id = self.id
                res = self._create_picking()
                results.append(res)

            else:
                results.append(False)
        return results

    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        shipment_line = self.env['shipment.advice.line'].search([('id', 'in', tuple(self.shipment_lines.ids))],
                                                                order="purchase_id desc")
        picking = False
        for line in shipment_line:
            for order in line.purchase_id.filtered(lambda po: po.state in ('purchase', 'done')):
                if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                    order = order.with_company(order.company_id)
                    pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                    res = order._prepare_picking()
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    if not pickings:
                        res = order._prepare_picking()
                        picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    else:
                        picking = pickings[0]
                    moves = line._create_stock_moves(picking)
                    picking.picking_type_id = self.picking_type_id.id
                    picking._onchange_picking_type()
                    picking.shipment_id = self.id
                    picking.po_boe_type = self.boe_type
                    picking.po_boe_no = self.boe_no
                    picking.po_ship_no = self.ship_no
                    # picking.boe_id = self.bill_of_entry_id
                    moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date):
                        seq += 5
                        move.sequence = seq

        return True

    # def _create_picking(self):
    #
    #     StockPicking = self.env['stock.picking']
    #     shipment_line = self.env['shipment.advice.line'].search([('id', 'in', tuple(self.shipment_lines.ids))],
    #                                                             order="purchase_id desc")
    #     for line in shipment_line:
    #         for order in line.purchase_id.filtered(lambda po: po.state in ('purchase', 'done')):
    #             if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
    #                 order = order.with_company(order.company_id)
    #                 pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
    #                 res = order._prepare_picking()
    #                 picking = StockPicking.with_user(SUPERUSER_ID).create(res)
    #                 pickings = picking
    #                 if not pickings:
    #                     res = order._prepare_picking()
    #                     picking = StockPicking.with_user(SUPERUSER_ID).create(res)
    #                 else:
    #                     picking = pickings[0]
    #                 moves = line._create_stock_moves(picking)
    #                 picking.picking_type_id = self.picking_type_id.id
    #                 picking._onchange_picking_type()
    #                 picking.shipment_id = self.id
    #                 picking.po_boe_type = self.boe_type
    #                 picking.po_boe_no = self.boe_no
    #                 picking.po_ship_no = self.ship_no
    #
    #                 moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
    #                 seq = 0
    #                 for move in sorted(moves, key=lambda move: move.date):
    #                     seq += 5
    #                     move.sequence = seq
    #
    #     return True

    def action_view_stock_moves(self):
        action = self.env.ref("stock.stock_move_action").sudo().read()[0]
        # remove default filters
        action["context"] = {}
        lines = self.shipment_lines.mapped("purchase_line_id.move_ids")
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [(self.env.ref("stock.view_move_form").id, "form")]
            action["res_id"] = lines.id
        return action

    def action_view_purchase(self):
        action = self.env.ref("purchase.purchase_form_action").sudo().read()[0]
        # remove default filters
        action["context"] = {}
        purchase_ids = self.shipment_lines.mapped("purchase_id")
        if len(purchase_ids) > 1:
            action["domain"] = [("id", "in", purchase_ids.ids)]
        elif purchase_ids:
            action["views"] = [(self.env.ref("purchase.purchase_order_form").id, "form")]
            action["res_id"] = purchase_ids.id
        return action

    def action_view_invoices(self):
        action = self.env.ref("account.action_move_in_invoice_type").sudo().read()[0]
        # remove default filters
        action["context"] = {}
        invoices = self.shipment_lines.mapped("purchase_id.invoice_ids")
        pickings = self.env['stock.picking'].search([('shipment_id', '=', self.id)])
        invoice_ids = invoices.search([('picking_id', 'in', pickings.ids)])
        if len(invoice_ids) > 1:
            action["domain"] = [("id", "in", invoice_ids.ids)]
        elif invoice_ids:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoice_ids.id
        else:
            return False
        return action

    def action_view_pickings(self):
        action = self.env.ref("stock.action_picking_tree_all").sudo().read()[0]
        # Remove default filters
        action["context"] = {}

        pickings = self.shipment_lines.filtered(lambda line: line.purchase_id and line.purchase_id.picking_ids)
        if len(pickings) > 1:
            action["domain"] = [("id", "in", pickings.mapped('purchase_id.picking_ids').ids)]
        elif pickings:
            picking = pickings[0].purchase_id.picking_ids[0]
            action["views"] = [(self.env.ref("stock.view_picking_form").id, "form")]
            action["res_id"] = picking.id
        else:
            return False

        return action

    boe_type = fields.Selection(
        [('internal', 'Internal Transfer'),
         ('import', 'Import'),
         ], string="Bill Of Entry Type")

    boe_no = fields.Char('Bill Of Entry NO')
    ship_no = fields.Char('Shipping Doc NO')

    def set_boe_number(self):
        for order in self:
            if order.picking_ids:
                order.picking_ids.write({'po_boe_type': order.boe_type,
                                         'po_boe_no': order.boe_no,
                                         'po_ship_no': order.ship_no,

                                         })


    def open_boe(self):
        return {
            'name': 'BOE',
            'type': 'ir.actions.act_window',
            'res_model': 'boe.wizard',
            'view_mode': 'form',
            'context': {'default_purchase_ids': self.ids, },

            'target': 'new',
        }


class ShipmentAdviceLine(models.Model):
    _name = 'shipment.advice.line'
    _description = 'Shipment Advice Line'
    _rec_name = 'product_id'

    vendor_id = fields.Many2one('res.partner')
    shipment_id = fields.Many2one(
        'shipment.advice', 'Shipment', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    purchase_id = fields.Many2one('purchase.order', 'Purchase', ondelete='cascade', required=True, copy=False,
                                  domain="[('state', 'in', ('purchase', 'done'))]")
    purchase_line_id = fields.Many2one(
        'purchase.order.line', 'Product Description', required=True,
        domain="[('order_id', '=', purchase_id), ('order_id', '=', purchase_id), ('product_id', '=', product_id)]")
    company_id = fields.Many2one(related='shipment_id.company_id')
    product_packaging_id = fields.Many2one(related='purchase_line_id.product_packaging_id')
    open_packaging_qty = fields.Float(string='Open Qty', readonly=1)
    shipped_packaging_qty = fields.Float(string='Shipped Qty', digits='Product Unit of Measure')
    received_qty = fields.Float(string='Rec. Qty(Unit)', digits='Product Unit of Measure',
                                related='purchase_line_id.qty_received')
    received_packaging_qty = fields.Float(string='Received Qty', digits='Product Unit of Measure')
    inspected_packaging_qty = fields.Float(string='Inspected Qty', digits='Product Unit of Measure')
    is_inspected = fields.Boolean(string='Inspected', default=False)
    state = fields.Selection(string='Shipment Status', related='shipment_id.state')

    arrival_date_shipment = fields.Date(related='shipment_id.arrival_date', string='Arrival Date')
    is_goods_in_transit_open = fields.Boolean(default=False)
    balance_qty = fields.Float(string='Balance Qty', compute="get_balance_qty", store=True)
    price = fields.Float(string='Price')
    amount = fields.Float(string='Amount')
    shipment_lines = fields.One2many(comodel_name='shipment.advice.line', inverse_name='shipment_id',
                                     string='Shipment Products', required=False, tracking=True)

    @api.depends('open_packaging_qty', 'shipped_packaging_qty')
    def get_balance_qty(self):
        for line in self:
            if line.open_packaging_qty and line.shipped_packaging_qty:
                line.balance_qty = line.open_packaging_qty - line.shipped_packaging_qty

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            po_lines = self.env['purchase.order.line'].search(
                [('order_id.state', 'in', ('purchase', 'done')),
                 ('product_id', '=', self.product_id.id)])
            po_line_ids = po_lines.filtered(lambda l: (l.product_uom_qty - l.shipment_adv_qty) > 0)
            return {
                'domain': {
                    'purchase_id': [('id', 'in', po_line_ids.mapped('order_id').ids)]
                }
            }

    @api.onchange('purchase_line_id')
    def _onchange_purchase_line_id(self):
        open_packaging_qty = 0.0
        received_qty_packaged = 0.0
        if self.purchase_line_id:
            # packaging_uom = self.product_packaging_id.product_uom.id
            open_qty = self.purchase_line_id.product_uom_qty - self.purchase_line_id.shipment_adv_qty
            # packaging_uom_qty = self.purchase_line_id.product_uom._compute_quantity(open_qty, packaging_uom)
            open_packaging_qty = open_qty
            # received_qty = self.purchase_line_id.qty_received
            # received_qty_converted = self.purchase_line_id.product_uom._compute_quantity(received_qty, packaging_uom)
            # received_qty_packaged = float_round(received_qty_converted / self.product_packaging_id.qty,
            #                                     precision_rounding=packaging_uom.rounding)
        self.update({
            'open_packaging_qty': open_packaging_qty,
            'shipped_packaging_qty': open_packaging_qty,
            'received_packaging_qty': received_qty_packaged,
        })

    @api.onchange('shipped_packaging_qty')
    def _onchange_shipped_packaging_qty(self):
        result = {}
        if self.shipped_packaging_qty > self.open_packaging_qty:
            result['warning'] = {
                'title': _('Warning'),
                'message': _('Shipped quantity should not be exceed open qty.'),
            }
        return result

    def _create_stock_moves(self, picking):
        values = []
        for line in self.purchase_line_id.filtered(lambda l: not l.display_type):
            for val in self._prepare_stock_moves(line, picking):
                values.append(val)
            line.move_dest_ids.created_purchase_line_ids = False
        return self.env['stock.move'].create(values)

    # def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
    #     print("pppppppppppppp")
    #     """Overrides to inject inspected qty to stock_move_line."""
    #
    #     self.ensure_one()
    #     po_line = self.purchase_line_id
    #     details_list = []
    #     final_qty = self.received_packaging_qty
    #     product_summary = self.env['shipment.advice.summary'].search(
    #         [('shipment_id', '=', self.shipment_id.id), ('product_id', '=', po_line.product_id.id)])
    #
    #     for line in product_summary:
    #         for inline in line.summary_lines:
    #             if final_qty > inline.remaining_qty:
    #                 qty_done = inline.remaining_qty
    #                 final_qty = final_qty - inline.remaining_qty
    #                 inline.remaining_qty = 0
    #             else:
    #                 qty_done = final_qty
    #                 inline.remaining_qty = inline.remaining_qty - final_qty
    #                 final_qty = 0
    #             if qty_done > 0:
    #                 # lot = self.env['stock.production.lot'].search(
    #                 #     [('name', '=', inline.lot_name), ('company_id', '=', self.env.company.id),
    #                 #      ('product_id', '=', po_line.product_id.id)])
    #                 # if len(lot) == 0:
    #                 #     lot = self.env['stock.production.lot'].create(
    #                 #         {'name': inline.lot_name, 'company_id': self.env.company.id,
    #                 #          'expiration_date': inline.expiry_date, 'product_id': po_line.product_id.id})
    #                 details_list.append((0, 0, {'picking_id': picking.id,
    #                                             'product_id': po_line.product_id.id, 'qty_done': qty_done,
    #                                             'lot_name': inline.lot_name,
    #                                             'product_uom_id': product_uom.id,
    #                                             'location_id': po_line.order_id.partner_id.property_stock_supplier.id,
    #                                             'location_dest_id': (po_line.orderpoint_id and not (
    #                                                     po_line.move_ids | po_line.move_dest_ids)) and po_line.orderpoint_id.location_id.id or po_line.order_id._get_destination_location(), }))
    #     po_line._check_orderpoint_picking_type()
    #     product = po_line.product_id.with_context(lang=po_line.order_id.dest_address_id.lang or self.env.user.lang)
    #     date_planned = po_line.date_planned or po_line.order_id.date_planned
    #     valu = {
    #         'name': (po_line.name or '')[:2000],
    #         'product_id': po_line.product_id.id,
    #         'date': date_planned,
    #         'date_deadline': date_planned,
    #         'location_id': po_line.order_id.partner_id.property_stock_supplier.id,
    #         'location_dest_id': (po_line.orderpoint_id and not (
    #                 po_line.move_ids | po_line.move_dest_ids)) and po_line.orderpoint_id.location_id.id or po_line.order_id._get_destination_location(),
    #         'picking_id': picking.id,
    #         'partner_id': po_line.order_id.dest_address_id.id,
    #         'move_dest_ids': [(4, x) for x in po_line.move_dest_ids.ids],
    #         'state': 'draft',
    #         'purchase_line_id': po_line.id,
    #         'company_id': po_line.order_id.company_id.id,
    #         'price_unit': price_unit,
    #         'picking_type_id': po_line.order_id.picking_type_id.id,
    #         'group_id': po_line.order_id.group_id.id,
    #         'origin': po_line.order_id.name,
    #         'description_picking': product.description_pickingin or po_line.name,
    #         'propagate_cancel': po_line.propagate_cancel,
    #         'warehouse_id': po_line.order_id.picking_type_id.warehouse_id.id,
    #         'product_uom_qty': product_uom_qty,
    #         'product_uom': product_uom.id,
    #         'move_line_nosuggest_ids': details_list
    #     }
    #     print(valu,"valu")
    #     return valu

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        """Overrides to inject inspected qty to stock_move_line."""

        self.ensure_one()
        po_line = self.purchase_line_id
        details_list = []
        final_qty = self.received_packaging_qty
        product_summary = self.env['shipment.advice.summary'].search(
            [('shipment_id', '=', self.shipment_id.id), ('product_id', '=', po_line.product_id.id)])

        for line in product_summary:
            # for inline in line.summary_lines:
            #     if final_qty > inline.remaining_qty:
            open_qty = self.purchase_line_id.product_uom_qty - self.purchase_line_id.shipment_adv_qty
            #         final_qty = final_qty - inline.remaining_qty
            #         inline.remaining_qty = 0
            #     else:
            #         qty_done = final_qty
            #         inline.remaining_qty = inline.remaining_qty - final_qty
            #         final_qty = 0
            if open_qty > 0:
                # lot = self.env['stock.production.lot'].search(
                #     [('name', '=', inline.lot_name), ('company_id', '=', self.env.company.id),
                #      ('product_id', '=', po_line.product_id.id)])
                # if len(lot) == 0:
                #     lot = self.env['stock.production.lot'].create(
                #         {'name': inline.lot_name, 'company_id': self.env.company.id,
                #          'expiration_date': inline.expiry_date, 'product_id': po_line.product_id.id})
                details_list.append((0, 0, {'picking_id': picking.id,
                                            'product_id': po_line.product_id.id,
                                            # 'quantity': qty_done,
                                            'date': datetime.now(),
                                            # 'lot_name': inline.lot_name,
                                            'product_uom_id': product_uom.id,
                                            'location_id': po_line.order_id.partner_id.property_stock_supplier.id,
                                            'location_dest_id': (po_line.orderpoint_id and not (
                                                    po_line.move_ids | po_line.move_dest_ids)) and po_line.orderpoint_id.location_id.id or po_line.order_id._get_destination_location(), }))
        po_line._check_orderpoint_picking_type()
        product = po_line.product_id.with_context(lang=po_line.order_id.dest_address_id.lang or self.env.user.lang)
        date_planned = po_line.date_planned or po_line.order_id.date_planned
        return {
            'name': (po_line.name or '')[:2000],
            'product_id': po_line.product_id.id,
            'date': date_planned,
            'date_deadline': date_planned,
            'location_id': po_line.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': (po_line.orderpoint_id and not (
                    po_line.move_ids | po_line.move_dest_ids)) and po_line.orderpoint_id.location_id.id or po_line.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': po_line.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in po_line.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': po_line.id,
            'company_id': po_line.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': po_line.order_id.picking_type_id.id,
            'group_id': po_line.order_id.group_id.id,
            'origin': po_line.order_id.name,
            'description_picking': product.description_pickingin or po_line.name,
            'propagate_cancel': po_line.propagate_cancel,
            'warehouse_id': po_line.order_id.picking_type_id.warehouse_id.id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uom.id,
            'move_line_ids': details_list
        }

    def _prepare_stock_moves(self, line, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        price_unit = line._get_stock_move_price_unit()
        packaging_uom = self.product_packaging_id.product_uom_id
        qty_per_packaging = self.product_packaging_id.qty
        inspected_qty = packaging_uom._compute_quantity(self.received_packaging_qty,
                                                        self.purchase_line_id.product_uom)
        product_uom_qty, product_uom = line.product_uom._adjust_uom_quantities(inspected_qty,
                                                                               self.product_id.uom_id)

        move_vals = self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        res.append(move_vals)
        return res

    def _prepare_account_move_line(self, move=False, qty_to_invoice=0.0):
        self.ensure_one()
        po_line = self.purchase_line_id
        aml_currency = move and move.currency_id or po_line.currency_id
        date = move and move.date or fields.Date.today()

        res = {
            'display_type': po_line.display_type,
            'sequence': po_line.sequence,
            'name': '%s: %s' % (po_line.order_id.name, po_line.name),
            'product_id': po_line.product_id.id,
            'product_uom_id': po_line.product_uom,
            'quantity': qty_to_invoice,
            'price_unit': po_line.currency_id._convert(po_line.price_unit, aml_currency, po_line.company_id, date,
                                                       round=False),
            'tax_ids': [(6, 0, po_line.taxes_id.ids)],
            'analytic_account_id': po_line.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, po_line.analytic_tag_ids.ids)],
            'purchase_line_id': po_line.id,
            'discount': po_line.discount,
        }
        if not move:
            return res

        if po_line.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res


class ShipmentAdviceTotal(models.Model):
    _name = 'shipment.advice.summary'
    _description = 'Shipment Advice Total'
    _rec_name = 'product_id'

    shipment_id = fields.Many2one(
        'shipment.advice', 'Shipment', ondelete='cascade', required=True)
    shipment_line_ids = fields.Many2many('shipment.advice.line', string='Shipment Lines')
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)],
                                 change_default=True)
    product_packaging_id = fields.Many2one('product.packaging', string='Packaging',
                                           domain="[('purchase', '=', True), ('product_id', '=', product_id)]",
                                           check_company=True)
    shipped_packaging_qty = fields.Float(string='Shipped Qty', digits='Product Unit of Measure')
    received_packaging_qty = fields.Float(string='Received Qty', digits='Product Unit of Measure',
                                          )
    scrapped_package_qty = fields.Float(string='Shortage Qty', digits='Product Unit of Measure')
    state = fields.Selection(string='Shipment Status', related='shipment_id.state')
    reason = fields.Char()
    shipment_lines = fields.One2many(comodel_name='shipment.advice.line', inverse_name='shipment_id',
                                     string='Shipment Products', required=False, tracking=True)

    @api.onchange('shipped_packaging_qty', 'scrapped_package_qty')
    def _get_received_qty(self):
        for rec in self:
            rec.received_packaging_qty = rec.shipped_packaging_qty - rec.scrapped_package_qty

    @api.onchange('received_packaging_qty')
    def _get_qty_done(self):
        for rec in self:
            if rec.received_packaging_qty:
                for line in rec.summary_lines:
                    line.qty_done = rec.received_packaging_qty
                    line.remaining_qty = rec.received_packaging_qty


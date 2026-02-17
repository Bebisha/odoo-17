from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class MaterialPurchaseRequisition(models.Model):
    _inherit = "material.purchase.requisition"

    def _get_buyer_domain(self):
        purchase_manager = self.env.ref('purchase.group_purchase_manager').users
        purchase_user = self.env.ref('purchase.group_purchase_user').users
        user_ids = []
        for usr in purchase_user:
            if usr.id not in purchase_manager.ids:
                user_ids.append(usr.id)
        return [('id', 'in', user_ids)]

    project_id = fields.Many2one('project.project')
    analytic_count = fields.Integer(string="Analytic Line", compute='compute_analytic_count', )
    bom_id = fields.Many2one('bom.selection')
    purchase_user_id = fields.Many2one('res.users', string='Purchase Representative', domain=_get_buyer_domain)
    show_decorations = fields.Boolean('Show Decorations', default=False)
    is_fully_available = fields.Boolean('Fully Available')
    purchase_order_count = fields.Integer('Purchase Order', compute='_get_purchase_order_count')
    is_rfq_needed = fields.Boolean('Is Rfq needed')
    is_check_availablity = fields.Boolean('Is Check Availablity')
    is_check_availablity_2 = fields.Boolean('Is Check Availablity')
    is_tranfer = fields.Boolean('Is Tranfer')
    anyone_fully_avilable = fields.Boolean('Fully avilable')
    reserved_quantity = fields.Float('Reserved Quantity')

    all_rfq = fields.Boolean('All RFQ')
    is_transfer = fields.Boolean('Is Transfer')
    is_picking_needed = fields.Boolean('Is Picking', default=False)
    is_fully_transfer = fields.Boolean('Is fully transfer', default=False, compute='compute_is_fully_transfer')


    is_fully_available = fields.Boolean('Fully Available', readonly=True,default=False,copy=False)
    is_rfq_needed = fields.Boolean('Is Rfq needed', readonly=True,default=False,copy=False)

    def compute_is_fully_transfer(self):
        for rec in self:
            rec.is_fully_transfer = False
            stock = self.env['stock.picking'].search(
                [('id', 'in', rec.picking_ids.ids), ('state', '!=', 'cancel')]).mapped('state')
            if stock:
                all_done = all(status == 'done' for status in stock)

                if all_done:
                    # if all(mr_count)=='done':
                    rec.is_fully_transfer = True

    @api.depends('requisition_line_ids')
    def _compute_all_fully_available(self):
        for requisition in self:
            # requisition.is_fully_available = False
            requisition.is_transfer = False
            requisition.is_rfq_needed = False
            if any(line.is_fully_available for line in requisition.requisition_line_ids):
                requisition.is_fully_available = True
                requisition.is_check_availablity = False

            # if any(line.is_rfq_needed for line in requisition.requisition_line_ids) and not requisition.is_transfer:
            #     requisition.is_rfq_needed = True
            if any(line.is_fully_available and not line.is_tranfer for line in requisition.requisition_line_ids):
                requisition.is_transfer = True
                requisition.is_check_availablity = False

            # elif any(line.is_fully_available and line.is_tranfer for line in requisition.requisition_line_ids):
            #     requisition.is_transfer = False

            if any(line.is_rfq_needed for line in requisition.requisition_line_ids) and not requisition.is_transfer:
                requisition.is_rfq_needed = True
                requisition.is_check_availablity = False
            #
            if all(not line.is_rfq_needed for line in requisition.requisition_line_ids):
                requisition.is_picking_needed = True

            # requisition.is_transfer = True

    all_fully_available = fields.Boolean(string="All Fully Available", compute='_compute_all_fully_available',
                                         store=False)

    def _get_purchase_order_count(self):
        for rec in self:
            po_ids = self.env['purchase.order'].search([]).filtered(
                lambda x: rec.id in x.requisition_po_id.ids)
            rec.purchase_order_count = len(po_ids)

    def compute_analytic_count(self):
        for record in self:
            record.analytic_count = False
            account_id = self.env['account.analytic.account'].search([('name', '=', self.project_id.name)])

            record.analytic_count = self.env['account.analytic.line'].search_count(
                [('account_id', '=', account_id.id), ('material_request_line_ids', 'in', record.id)])

    def action_final_move_record(self):
        self.ensure_one()
        move_id = self.env['stock.move'].search([('material_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Moves',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'domain': [('id', 'in', move_id.ids)],
            'context': "{'create': False}"
        }

    def action_get_analytic_record(self):
        self.ensure_one()
        account_id = self.env['account.analytic.account'].search([('name', '=', self.project_id.name)])
        # self.account_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Analytic Line',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line',
            'domain': [('account_id', '=', account_id.id), ('material_request_line_ids', 'in', self.id)],
            'context': "{'create': False}"
        }

    def purchase_order_button(self):
        self.ensure_one()
        po_ids = self.env['purchase.order'].search([]).filtered(
            lambda x: x.requisition_po_id.id == self.id or self.id in x.requisition_po_id.ids)
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', po_ids.ids)],
        }

    purchase_order_ids = fields.Many2many('purchase.order', compute='_compute_purchase_orders',
                                          string='Related Purchase Orders')

    @api.depends('requisition_line_ids')
    def _compute_purchase_orders(self):
        for requisition in self:
            po_ids = self.env['purchase.order'].search([
                ('requisition_po_id', '=', requisition.id)
            ])
            requisition.purchase_order_ids = [(6, 0, po_ids.ids)]

    def validationerrorrfq(self):
        error_messages = []
        existing_draft_pos = self.env['purchase.order'].search([
            ('state', '!=', 'cancel'),
            # ('order_line.product_qty', '>', 0)
        ])

        processed_po_names = set()  # To keep track of processed po.names

        for line in self.requisition_line_ids:
            existing_draft_pos = existing_draft_pos.filtered(
                lambda x: any(rec.req_line_id == str(line.id) for rec in x.order_line))

            for po in existing_draft_pos:
                if po.name in processed_po_names:
                    continue  # Skip if we've already processed this po.name

                if not po.picking_ids:
                    if po.state not in ['done']:
                        error_messages.append(f'GIT is not created for this PO {po.name}')
                        processed_po_names.add(po.name)

                else:

                    all_pickings_done = all(picking.state == 'done' for picking in po.picking_ids)
                    if not all_pickings_done:
                        error_messages.append(f'Not all pickings are done for PO {po.name}')
                        processed_po_names.add(po.name)

        if error_messages:
            raise ValidationError('\n'.join(error_messages))

        self.is_check_availablity = False

    def check_availability(self):
        self.show_decorations = True
        self.is_check_availablity = True
        self.anyone_fully_avilable = True

        for rec in self.requisition_line_ids:
            project_loc = self.env['stock.location'].search([('is_project_location', '=', False),('usage','in',['internal', 'transit'])])
            stock_quant = self.env['stock.quant'].search(
                [('product_id', '=', rec.product_id.id),
                  ('location_id', 'in', project_loc.ids)])
            stock_reserve = self.env['stock.move.line'].search(
                [('product_id', '=', rec.product_id.id),('picking_id.picking_type_code','=','outgoing'),('state', '=', 'assigned')])
            if stock_quant and project_loc:
                rec.stock_qty = sum(stock_quant.mapped('inventory_quantity_auto_apply')) - sum(stock_reserve.mapped('quantity'))
            if rec.stock_qty < rec.qty:
                rec.is_rfq_needed = True
                rec.is_fully_available = False
            else:
                rec.is_rfq_needed = False
                rec.is_fully_available = True


        if any(line.is_rfq_needed == True for line in self.requisition_line_ids):
            self.is_rfq_needed = True
        else:
            self.is_rfq_needed = False
        if  any(line.is_fully_available == False for line in self.requisition_line_ids):
            self.is_fully_available = False
        else:
            self.is_fully_available = True


    def check_qunt(self):
        rfq_not_need = self.requisition_line_ids.mapped('is_rfq_needed')
        is_fully_satisfied = self.requisition_line_ids.mapped('is_fully_available')
        self.is_fully_available = False
        self.is_rfq_needed = False
        if any(rfq_not_need):
            self.is_rfq_needed = True

        if any(is_fully_satisfied):
            self.is_fully_available = True
        if all(is_fully_satisfied):
            self.write({
                'state': 'done'})

    def action_reset_draft(self):
        res = super(MaterialPurchaseRequisition, self).action_reset_draft()
        self.is_rfq_needed = False
        self.is_fully_available = False

        return res

    def _prepare_move_line_values(self,line,location,location_dest):
        self.ensure_one()
        move_line = self.env['stock.move.line'].search([('product_id','=',line.product_id.id),('location_dest_id','=',location.id),('picking_id','in',self.picking_ids.ids),('state','=','done')])
        line_list = []
        for line in move_line:
            line_list.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom_id.id,
                'quantity': line.quantity,
                'location_id': location.id,
                'location_dest_id': location_dest.id,
                'lot_id': line.lot_id.id,
            }))
        return line_list


    def done_visible_button(self):
        print("kkkkkkkkkkk")
        for requisition in self:
            project_locations = requisition.project_id.stock_location_id
            # visual_location = self.env.ref('kg_project.kg_stock_location_location5')
            project_production_location = self.env['stock.location'].search(
                [('is_project_production_location', '=', True), ('active', '=', True)], limit=1)
            for rec in self.requisition_line_ids:
                vals = {
                    'name': rec.description,
                    'account_id': rec.analytic_id.id,
                    'amount': rec.price_unit,
                    'date': self.requisition_date,
                    'unit_amount': rec.qty,
                    'product_id': rec.product_id.id,
                    'product_uom_id': rec.uom_id.id,
                    'material_request_line_id': self.id,
                    'material_request_line_id': self.id
                }
                print(vals,"vals")
                analytic = self.env['account.analytic.line'].create(vals)
                move_lines = self._prepare_move_line_values(rec,project_locations,project_production_location)
                print(move_lines,"move_lines")
                print( self.issue_location.id,"project_locations.id if project_locations else requisition.issue_location.id,")
                move = self.env['stock.move'].create(
                    {
                        'name': self.sequence,
                        'origin': self.sequence,
                        'company_id': self.company_id.id,
                        'product_id': rec.product_id.id,
                        'product_uom': rec.uom_id.id,
                        'material_id':self.id,
                        'state': 'draft',
                        'picked':True,
                        'product_uom_qty': rec.qty,
                        'location_id': project_locations.id if project_locations else requisition.issue_location.id,
                        'location_dest_id': project_production_location.id,
                    }
                    )

                print(move,"move_lines")
                move.move_line_ids = move_lines
                move._action_done()

            self.write({
                'state': 'done'})

        return True

    is_done = fields.Boolean('Done')

    def done_visible(self):
        fully_tyranfer = self.requisition_line_ids.mapped('transfer_created')
        if all(fully_tyranfer):
            self.is_done = True

    def action_done(self):
        print("ooooooooooooooo")
        for requisition in self:

            if not requisition.is_dm_approve:
                raise UserError(_("Please get the Material Request Approved before Confirmation"))

            if requisition.is_fully_available and not requisition.is_tranfer:
                print("uuuuuuuuuuuu")
                internal = self.env.ref('kg_project.stock_picking_material_issue').id
                print(internal,"internal")
                des = requisition.project_id.stock_location_id
                print(des,"des")
                des_loc = requisition.department_res_id.destination_location_id
                print(des_loc,"des_loc")
                soc = requisition.picking_type_id.default_location_dest_id
                print(soc,"soc")

                delivery_order = self.env['stock.picking'].create({
                    'partner_id': self.employee_id.user_partner_id.id,
                    'picking_type_id': internal,
                    'mr_id': requisition.id,
                    'location_id': soc.id,
                    'location_dest_id': des.id if des else des_loc.id,
                })
                print(delivery_order,"delivery_order")

                for line in requisition.requisition_line_ids:
                    if line.is_fully_available and not line.transfer_created:
                        delivery_order_line = self.env['stock.move'].create({
                            'name': line.product_id.name,
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.qty,
                            'quantity': line.qty,
                            'picking_id': delivery_order.id,
                            'location_id': soc.id,
                            'location_dest_id': des.id if des else des_loc.id,
                        })
                        print(delivery_order_line,"delivery_order_line")
                        line.is_tranfer = True
                        line.transfer_created = True

                delivery_order.action_confirm()
                delivery_order.button_validate()
                requisition.picking_ids = [(4, delivery_order.id)]
                requisition.is_transfer = False

                if any(line.is_rfq_needed for line in requisition.requisition_line_ids) and not requisition.is_transfer:
                    requisition.is_check_availablity = True
                requisition.write({
                    'state': 'transfer',
                    'completion_date': datetime.now()
                })



class RequisitionLine(models.Model):
    _inherit = "requisition.line"

    analytic_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                  compute='compute_analytic_account')
    delivery_date = fields.Date('Delivery Date')
    project_id = fields.Many2one('project.project', related='requisition_id.project_id')

    stock_qty = fields.Float('stock_qty')
    show_decorations = fields.Boolean('Show Decorations', related='requisition_id.show_decorations')
    ordered_qty = fields.Float(compute='compute_ordered_qty')
    is_fully_available = fields.Boolean('Fully Available', readonly=True,default=False,copy=False)
    is_rfq_needed = fields.Boolean('Is Rfq needed', readonly=True,default=False,copy=False)
    qty_needed_for_mr = fields.Float('Quantity Needed')
    reserve_qty = fields.Float('Reserve Qty')
    is_reserve = fields.Boolean('Is reserve')
    is_tranfer = fields.Boolean('Is Transfer')
    transfer_created = fields.Boolean('Is Transfer')
    update_picking_qty = fields.Float('update picking qty', compute='compute_update_picking_qty')

    def compute_update_picking_qty(self):
        for rec in self:
            rec.update_picking_qty = False
            existing_draft_pos = self.env['purchase.order.line'].search(
                [('state', '!=', 'cancel')])
            rec.update_picking_qty = sum(existing_draft_pos.filtered(
                lambda x: x.req_line_id == str(rec.id)).mapped('product_qty'))

    def action_reserve(self):
        self.is_reserve = False

    def action_unreserve(self):
        self.is_reserve = True

    @api.depends('project_id')
    def compute_analytic_account(self):
        for order in self:
            order.analytic_id = False

            if order.project_id:
                if not order.requisition_id.id:
                    raise UserError("Please save the Material Requisition before computing the analytic account.")

                analytic_pool = self.env['account.analytic.account']
                plan_id = self.env['account.analytic.plan'].search(
                    [('company_id', '=', order.requisition_id.company_id.id)], limit=1)
                if not plan_id:
                    raise UserError("Analytic account plan is not configured for the logged-in user's company.")

                analytic_val = {
                    'name': order.project_id.name,
                    'plan_id': plan_id.id,
                    'material_request_line_ids': [(4, order.requisition_id.id)]
                }

                analytic = analytic_pool.search([('name', '=', order.project_id.name)], limit=1)
                if not analytic:
                    analytic = analytic_pool.create(analytic_val)

                analytic.write({
                    'material_request_line_ids': [(4, order.requisition_id.id)]
                })

                if not order.analytic_id:
                    order.analytic_id = analytic

    def compute_ordered_qty(self):
        for rec in self:
            rec.ordered_qty = False
            po_ids = self.env['purchase.order'].search([]).filtered(
                lambda x: x.requisition_po_id.id == rec.requisition_id.id or rec.id in x.requisition_po_id.ids)

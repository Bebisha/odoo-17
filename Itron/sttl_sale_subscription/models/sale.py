from dateutil.relativedelta import relativedelta

from odoo import fields, models, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError,ValidationError


import logging

_logger = logging.getLogger(__name__)


class Sale(models.Model):
    _inherit = 'sale.order'

    recurrance_id = fields.Many2one(comodel_name='product.subscription.period', string='Recurrence Period')
    start_date = fields.Date(string='Start Date',readonly=False)
    date_start = fields.Date(string="Start Date")
    recurr_until = fields.Date(string='End Date')
    next_invoice_date = fields.Date(string='Next Invoice Date' ,copy=False)
    recurring_started = fields.Boolean(string='Recurring Started')
    subscription_status = fields.Selection(string='Subscription Status',
                                           selection=[('a', 'Pending'), ('b', 'Running'), ('c', 'End')], default="a",
                                           copy=False)
    sale_type = fields.Selection([('project', 'Project'), ('contract', 'Contract'), ('success', 'Success Pack')],
                                 'Sale Type')
    project_type = fields.Selection([('onsite', 'Onsite'), ('amc', 'AMC'), ('offshore', 'Offshore'), ('free_support', 'Free Support')],
                                    'Contract Type')
    planned_hrs = fields.Float('Planned Hours')
    closing_date = fields.Date(string='Closing Date', default='', copy=False)
    contract_request_count = fields.Integer(string="Onsite", compute="_compute_contract_request_count")
    contract_request_amc_count = fields.Integer(string="AMC", compute="_compute_contract_request_amc_count")
    contract_request_offshore_count = fields.Integer(string="Offshore",
                                                     compute="_compute_contract_request_offshore_count")
    contract_request_free_count = fields.Integer(string="Free Support",
                                                     compute="_compute_free_support_count")
    contract_request_ids = fields.One2many('project.contract.request', 'sale_id', string="Contract Requests")
    contract_request_amc_ids = fields.One2many('project.contract.request.amc', 'sale_id', string="Contract Requests")
    contract_request_free_ids = fields.One2many('project.contract.request.free.support', 'sale_id', string="Free Support")
    is_fully_paid = fields.Boolean(default=False, compute='compute_payment_status')
    payment_status = fields.Selection([
        ('partial', 'Partially Paid'),
        ('full', 'Paid')
    ], string="Payment Status" ,)

    current_invoice_status = fields.Selection([
        ('paid', 'Paid'),
        ('not_paid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('no_invoice', 'No Invoice'),
    ], string="Current Invoice Status", compute="_compute_current_invoice_status", store=True)

    @api.depends('invoice_ids.invoice_date', 'recurrance_id.duration', 'invoice_ids.invoice_date_due',
                 'invoice_ids.payment_state')
    def _compute_current_invoice_status(self):
        print("status checkkkkkkkkkkkkkkkkk")
        today = date.today()
        print("ffffffffffffffffffffffff",self)

        for order in self:
            print("duration",order.recurrance_id.duration )
            duration = order.recurrance_id.duration or 1  # Default to 1 month if not set
            matched_invoices = []

            for inv in order.invoice_ids.filtered(lambda i: i.invoice_date):
                start_date = inv.invoice_date
                print("start_date",start_date)
                end_date = start_date + relativedelta(months=duration)
                if start_date <= today < end_date:
                    print("enteringggggggggggg")
                    matched_invoices.append(inv)
            print("matched_invoices",matched_invoices)

            if not matched_invoices:
                order.current_invoice_status = 'no_invoice'
            else:
                payment_states = [inv.payment_state for inv in matched_invoices]
                print(f'Order {order.name} - Matching invoice states:', payment_states)

                if all(state == 'paid' for state in payment_states):
                    order.current_invoice_status = 'paid'
                elif all(state == 'not_paid' for state in payment_states):
                    order.current_invoice_status = 'not_paid'
                else:
                    order.current_invoice_status = 'partial'



    def _compute_contract_request_count(self):
        for rec in self:
            rec.contract_request_count = self.env['project.contract.request'].search_count(
                [('sale_id', '=', rec.id), ('contract_type', '=', 'onsite')])

    def _compute_contract_request_amc_count(self):
        for rec in self:
            rec.contract_request_amc_count = self.env['project.contract.request.amc'].search_count(
                [('sale_id', '=', rec.id)])

    def _compute_contract_request_offshore_count(self):
        for rec in self:
            rec.contract_request_offshore_count = self.env['project.contract.request'].search_count(
                [('sale_id', '=', rec.id), ('contract_type', '=', 'offshore')])

    def _compute_free_support_count(self):
        print("_compute_free_support_count")
        for rec in self:
            rec.contract_request_free_count = self.env['project.contract.request.free.support'].search_count([('sale_id','=',rec.id)])




    def contract_request(self):
        self.ensure_one()
        requests = self.env['project.contract.request'].search(
            [('sale_id', '=', self.id), ('contract_type', '=', 'onsite')])

        if not requests:
            raise UserError("No Contract Requests found for this Sale Order.")

        if len(requests) == 1:
            return {
                'name': "Onsite",
                'type': 'ir.actions.act_window',
                'res_model': 'project.contract.request',
                'view_mode': 'form',
                'target': 'current',
                'res_id': requests.id,
            }
        else:
            return {
                'name': "Contract Requests",
                'type': 'ir.actions.act_window',
                'res_model': 'project.contract.request',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', requests.ids)],
                'target': 'current',
            }

    def contract_request_free_support(self):
        print("contract_request_free_support")
        self.ensure_one()
        requests = self.env['project.contract.request.free.support'].search([('sale_id', '=',self.id)])
        if not requests:
            raise UserError("No Free Support found for this Sale Order.")
        if len(requests) >= 1:
            return {
                'name': "Free Support",
                'type': 'ir.actions.act_window',
                'res_model': 'project.contract.request.free.support',
                'view_mode': 'tree,form',
                'target': 'current',
                # 'res_id': requests.id,
                'domain': [('id', 'in', requests.ids)],
            }

    def contract_request_offshore(self):
        self.ensure_one()
        requests = self.env['project.contract.request'].search(
            [('sale_id', '=', self.id), ('contract_type', '=', 'offshore')])

        if not requests:
            raise UserError("No Contract Requests found for this Sale Order.")

        if len(requests) == 1:
            return {
                'name': "Offshore",
                'type': 'ir.actions.act_window',
                'res_model': 'project.contract.request',
                'view_mode': 'form',
                'target': 'current',
                'res_id': requests.id,
            }
        else:
            # Open list view
            return {
                'name': "Contract Requests",
                'type': 'ir.actions.act_window',
                'res_model': 'project.contract.request',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', requests.ids)],
                'target': 'current',
            }

    def contract_request_amc(self):
        self.ensure_one()
        requests = self.env['project.contract.request.amc'].search(
            [('sale_id', '=', self.id), ('contract_type', '=', 'amc')])

        if not requests:
            raise UserError("No Contract Requests found for this Sale Order.")

        if len(requests) == 1:
            # Open single form
            return {
                'name': "Amc",
                'type': 'ir.actions.act_window',
                'res_model': 'project.contract.request.amc',
                'view_mode': 'form',
                'target': 'current',
                'res_id': requests.id,
            }
        else:
            # Open list view
            return {
                'name': "Contract Requests",
                'type': 'ir.actions.act_window',
                'res_model': 'project.contract.request.amc',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', requests.ids)],
                'target': 'current',
            }


    @api.onchange("order_line")
    def onchange_line_ids(self):
        recuring = non_recurring = False
        for rec in self.order_line:
            if rec.product_id:
                if rec.product_id.is_recurring:
                    recuring = True
                else:
                    non_recurring = True
        if recuring and non_recurring:
            raise UserError("Currently we don't support recurring and non recurring products together")

    @api.model_create_multi
    def create(self, vals):
        result = super(Sale, self).create(vals)
        for rec in result:
            recuring = non_recurring = False
            for line in rec.order_line:
                if line.product_id:
                    if line.product_id.is_recurring:
                        recuring = True
                    else:
                        non_recurring = True
            if recuring and non_recurring:
                raise UserError("Currently we don't support recurring and non recurring products togather")
        return result

    def write(self, vals):
        result = super(Sale, self).write(vals)
        for rec in self:
            recuring = non_recurring = False
            for line in rec.order_line:
                if line.product_id:
                    if line.product_id.is_recurring:
                        recuring = True
                    else:
                        non_recurring = True
            if recuring and non_recurring:
                raise UserError("Currently we don't support recurring and non recurring products together")
        return result

    # @api.onchange('recurrance_id')
    # def _onchange_recurrance_id(self):
    #     if self.recurrance_id:
    #         for rec in self.order_line:
    #             if rec.product_id.is_recurring:
    #                 price = self.env['product.subscription.pricing'].search(
    #                     [('period_id', '=', rec.order_id.recurrance_id.id), ('product_id', '=', rec.product_id.id)],
    #                     limit=1).price
    #                 rec.price_unit = price

    def action_create_recurring_invoices(self):
        today = date.today()

        for order in self:
            recurring_lines = order.order_line.filtered(
                lambda l: l.product_template_id.is_recurring and l.invoice_status == "to invoice"
            )

            if not recurring_lines:
                print("No recurring lines to invoice for order:", order.name)
                continue

            if not order.recurr_until:
                raise UserError("Please set a 'Recurring End Date' on the Sale Order.")

            next_invoice_date = order.next_invoice_date or order.date_start
            engagement_periods_raw = []
            ratio = False
            if  order.project_type == 'amc':
                ratio = order.recurrance_id.ratio if order.recurrance_id else 1

            while next_invoice_date <= order.recurr_until:
                invoice_lines = [
                    (0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.product_uom_qty / ratio if ratio else line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'name': line.name,
                        'tax_ids': [(6, 0, line.tax_id.ids)],
                        'sale_line_ids': [(6, 0, [line.id])],
                    }) for line in recurring_lines
                ]

                invoice = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': order.partner_id.id,
                    'invoice_date': next_invoice_date,
                    'invoice_date_due': next_invoice_date,
                    'date': next_invoice_date,
                    'invoice_origin': order.name,
                    'invoice_line_ids': invoice_lines,
                })

                if order.recurrance_id:
                    duration = order.recurrance_id.duration
                    unit = order.recurrance_id.unit

                    if unit == 'days':
                        invoice_end_date = next_invoice_date + timedelta(days=duration)
                    elif unit == 'weeks':
                        invoice_end_date = next_invoice_date + timedelta(weeks=duration)
                    elif unit == 'month':
                        invoice_end_date = next_invoice_date + relativedelta(months=duration)
                    elif unit == 'year':
                        invoice_end_date = next_invoice_date + relativedelta(years=duration)
                    else:
                        raise UserError("Invalid recurrence unit on Recurrence configuration.")
                else:
                    raise UserError("Please configure recurrence properly.")

                engagement_periods_raw.append({
                    'invoice_id': invoice.id,
                    'invoice_end_date': invoice_end_date,
                    'period_start_date': invoice.invoice_date,
                    'period_end_date': invoice_end_date,
                })

                next_invoice_date = invoice_end_date

            # Divide planned_hrs equally

            total_periods = len(engagement_periods_raw)
            per_period_hrs = order.planned_hrs / total_periods if total_periods else 0.0

            # Now convert to engagement_periods in expected format
            engagement_periods = [(0, 0, {
                **period,
                'planned_hours': per_period_hrs
            }) for period in engagement_periods_raw]

            contract_vals = {
                'partner_id': order.partner_id.id,
                'contract_type': order.project_type,
                'currency_id': order.currency_id.id,
                'recurrance_id': order.recurrance_id.id,
                'total_amount': 0.0,
                'sale_id': order.id,
                'date_contract': order.date_order,
                'engagement_period_ids': engagement_periods,
                'date_start': order.date_start,
                'date_end': order.recurr_until,
                'planned_hrs': order.planned_hrs,
            }

            if order.project_type == 'amc':
                self.env['project.contract.request.amc'].create(contract_vals)
            else:
                self.env['project.contract.request'].create(contract_vals)

    def action_confirm(self):
        res = super(Sale, self).action_confirm()
        for order in self:
            if order.sale_type == 'contract':
                if order.project_type == 'free_support':
                    self.action_create_free_support()
                else:
                    order.action_create_recurring_invoices()

        return res

    def action_create_free_support(self):
        self.ensure_one()
        print("action_create_free_support",self.start_date)
        for order in self:
            free_vals = {
                'partner_id': order.partner_id.id,
                'sale_id': order.id,
                'date_start': order.date_start if order.date_start else None,
                'date_end': order.recurr_until if order.recurr_until else None,
                'currency_id': order.currency_id.id if order.currency_id else order.env.company.currency_id.id,
                'company_id': order.company_id.id,
                'project_id': order.project_id.id,
                # 'description': 'Generated from Sale Order %s' % order.name,
            }
            print("sale_idsale_id",free_vals)

            # if order.project_type == 'free_support':
            #     print("gggggggggggggggggggggg")
            self.env['project.contract.request.free.support'].create(free_vals)

    def action_view_invoices_for_next_date(self):
        if not self.next_invoice_date:
            raise UserError("Next invoice date is not set.")

            # Search for invoices linked to this sale order with invoice_date = next_invoice_date
        invoices = self.env['account.move'].search([
            ('invoice_origin', '=', self.name),
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '=', self.next_invoice_date),
        ])

        if not invoices:
            raise UserError(f"No invoices found for next invoice date: {self.next_invoice_date}")
        return {

            'name': "View Invoice",
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_type': '',
            'view_mode': 'form',
            'target': 'current',
            'res_id': invoices.id
            # 'domain': [('id','in',invoices.ids)],

        }
        # Return action to open these invoices in tree/form view
        # action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        # action.update({
        #     'domain': [('id', 'in', invoices.ids)],
        #     'context': {'default_move_type': 'out_invoice'},
        #     'views': [(self.env.ref('account.view_move_form').id, 'form'),
        #               (self.env.ref('account.view_move_tree').id, 'tree')],
        # })
        # return action

    def generate_recurring_invoices(self):
        orders = self.env['sale.order'].search(
            [('next_invoice_date', '=', datetime.datetime.today().date()), ('state', '=', 'sale'),
             ('subscription_status', '=', 'b')])
        for order in orders:
            do_copied = False
            do_cpy = False
            for line in order.order_line:
                if not do_copied and line.product_id.is_recurring and line.invoice_status != "to invoice":
                    if line.product_id.type != 'service':
                        do_cpy = line.move_ids[
                            0].picking_id.copy()  # Copying 1 picking in order to avoid multiple pickings with same delivery
                        do_cpy.state = 'assigned'  # Change state to ready
                        do_copied = True
                        # Assign done qtties in order to validate automatically
                        for move in do_cpy.move_ids_without_package:
                            move.quantity_done = move.product_uom_qty
                    else:
                        if line.product_id.invoice_policy == 'order':
                            if not line.prev_added_qty:
                                line.prev_added_qty = line.product_uom_qty
                            line.product_uom_qty = line.product_uom_qty + line.prev_added_qty
                        else:
                            line.qty_delivered += line.product_uom_qty
                if line.product_id.invoice_policy == 'order':
                    qty = False
                    if do_cpy:
                        for do_cpy_line in do_cpy.move_ids_without_package:
                            if do_cpy_line.product_id == line.product_id:
                                qty = do_cpy_line.product_uom_qty

                        line.product_uom_qty += qty
                        self.action_invoice(order)

            # if do_cpy:
            #     do_cpy.button_validate()
            #     order.invoice_status = 'to invoice'

            self.action_invoice(order)
            # self.env.cr.commit()

            # End subscription is today is last recurring date
            if order.recurr_until and order.next_invoice_date:
                if order.recurr_until <= order.next_invoice_date:
                    order.subscription_status = 'c'

    def action_invoice(self, order):
        # Create Invoice if order is ready to be invoiced
        if order.invoice_status == 'invoiced':
            # invoice = self.env['sale.advance.payment.inv'] \
            # .with_context({
            #     'active_model': 'sale.order',
            #     'active_id': order.id,
            # }).create({})._create_invoices(order)
            invoice = order._create_invoices()
            invoice.action_post()
            invoice.invoice_status = 'invoiced'


    def end_subscription(self):
        return {
            'name': "Choose a Reason",
            'type': 'ir.actions.act_window',
            'res_model': 'close.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'rec_id': self.id
            },
        }

    def renew_subscription(self):
        # self.subscription_status = 'b'
        self.ensure_one()

        # Duplicate the order, excluding invoices, deliveries, etc.
        new_order = self.copy({
            'state': 'draft',  # Make sure it's a quotation
            'date_order': fields.Datetime.now(),
            # 'name': f"{self.name or ''}",
            'recurr_until': None,
            'subscription_status': 'a',
            'next_invoice_date': None,
            'invoice_status': 'no',  # Make sure the new order has no invoices
        })

        # Unlink any related records that you don't want copied, e.g., invoices, deliveries
        # Remove invoices (to avoid copying the invoice links)
        new_order.invoice_ids.unlink()

        # Remove related stock pickings (if any)
        new_order.picking_ids.unlink()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': new_order.id,
            'target': 'current',
        }

        # project_managers = self.project_id.user_id
        # print("project_managers",project_managers)
        # subject = f"Subscription Renewed: {self.name}"
        # body = f"""
        #                 <p>Dear <strong>{project_managers.name}</strong>,</p>
        #                 <p>Your Subscription <strong>{self.name}</strong> has been Successfully Renewed.</p>
        #             """
        # if project_managers.email:
        #     self.env['mail.mail'].sudo().create({
        #         'subject': subject,
        #         'body_html': body,
        #         'email_to': project_managers.email,
        #         'email_from': self.env.user.email ,
        #     }).send()

    def send_notification(self):
        default_duration = 10
        sale_orders = self.search([('next_invoice_date', '!=', False), ('subscription_status', '=', 'b')])
        notification_duration = self.env['ir.config_parameter'].get_param(
            'sttl_sale_subscription.notification_duration')
        if notification_duration == False:
            notification_duration = default_duration
        for order in sale_orders:
            date_diff = (order.next_invoice_date - date.today()).days
            if int(notification_duration) == date_diff:
                template_id = self.env.ref('sttl_sale_subscription.sale_subscription_notification_template').id
                template = self.env["mail.template"].browse(template_id)
                template.send_mail(order.id, force_send=True)

    # def send_invoice_post_notification(self):
    #     """
    #     Notify customer one day before invoice is posted
    #     """
    #     today = date.today()
    #     tomorrow = today + timedelta(days=1)
    #     partner_id = self.env['ir.config_parameter'].sudo().get_param(
    #         'sttl_sale_subscription.contract_app_ids'
    #     )
    #     if not partner_id:
    #         _logger.warning("No notification partner configured in system parameters.")
    #         return
    #
    #     partner = self.env['res.partner'].browse(int(partner_id))
    #     if not partner or not partner.email:
    #         _logger.warning("Configured partner is invalid or has no email.")
    #         return
    #     orders = self.search([
    #         ('next_invoice_date', '=', tomorrow),
    #         ('subscription_status', '=', 'b'),
    #         ('state', '=', 'sale')
    #     ])
    #     template = self.env.ref('sttl_sale_subscription.sale_subscription_invoice_1day_notice_template',
    #                             raise_if_not_found=False)
    #     if not template:
    #         _logger.warning("Email template not found: sale_subscription_invoice_1day_notice_template")
    #         return
    #     for order in orders:
    #         template.email_to = partner.email
    #         template.send_mail(order.id, force_send=True)

    #Dashboard function
    def get_contract_order_data(self):
        today = date.today()
        current_company_id = self.env.companies.ids
        domain = [

            # ('company_id', '=', current_company_id),
            ('sale_type', '=', 'contract'),
            ('state', '!=', 'cancel'),
        ]
        contracts = self.env['sale.order'].sudo().search(domain)
        customers = [{"id": customer.id, "name": customer.name} for customer in contracts.sudo().mapped('partner_id')]
        projects = [{"id": project.id, "name": project.name} for project in contracts.sudo().mapped('project_id')]
        contract_types = self._fields['project_type'].selection  # Returns list of tuples (key, value)
        contract_data = []
        for contract in contracts:
            currency_symbol = contract.currency_id.name if contract.currency_id else ''

            total_amount = round(contract.amount_total)
            amount_paid = round(contract.kg_total_received or 0.0, 2)
            pending_amount = max(0, round(total_amount - amount_paid, 2))
            # pending_amount = "{:,.2f}".format(pending_amount)
            # amount_paid = "{:,.2f}".format(amount_paid)
            # total_amount = "{:,.2f}".format(total_amount)
            total_amount = f"{total_amount:,.2f} {currency_symbol}"
            pending_amount = f"{pending_amount:,.2f} {currency_symbol}"
            amount_paid = f"{amount_paid:,.2f} {currency_symbol}"


            contract_data.append({
                'id': contract.id,
                'customers': contract.partner_id.name,
                'project_id': contract.project_id.name if contract.project_id else '',
                'project_id_id': contract.project_id.id if contract.project_id else 0,
                'contract_type_key': contract.project_type,
                'contract_type': dict(contract._fields['project_type'].selection).get(contract.project_type),
                'date_start': str(contract.date_start.strftime('%d/%m/%Y')) if contract.date_start else '',
                'date_end': str(contract.recurr_until.strftime('%d/%m/%Y')) if contract.recurr_until else '',
                'total': total_amount,
                'amount_paid': amount_paid,
                'kg_pending_amt': pending_amount,
                'next_invoice_date':str(contract.next_invoice_date.strftime('%d/%m/%Y')) if contract.next_invoice_date else '',
                'status': dict(contract._fields['current_invoice_status'].selection).get(
                    contract.current_invoice_status),
            })
            contract.sudo()._compute_current_invoice_status()

        # print("contracts", contracts)
        return {
            'contract_order_data': contract_data, 'customers': customers,
            'projects': projects, 'contract_types': list(contract_types),
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    prev_added_qty = fields.Float(string='Previous Added Qty')
    subscription_status = fields.Selection(string='Subscription Status',
                                           selection=[('a', 'Pending'), ('b', 'Running'), ('c', 'End')],
                                           related="order_id.subscription_status", store=True)
    sale_type = fields.Selection(related='order_id.sale_type', store=True)
    is_qty_readonly = fields.Boolean(compute='_compute_is_qty_readonly', store=False)

    @api.depends('order_id.sale_type')
    def _compute_is_qty_readonly(self):
        for line in self:
            line.is_qty_readonly = line.order_id.sale_type == 'contract'


    # def _compute_price_unit(self):
    #     super(SaleOrderLine, self)._compute_price_unit()
    #     for rec in self:
    #         if rec.product_template_id:
    #             if rec.product_template_id.is_recurring:
    #                 if rec.order_id.recurrance_id:
    #                     price = self.env['product.subscription.pricing'].search(
    #                         [('period_id', '=', rec.order_id.recurrance_id.id), ('product_id', '=', rec.product_id.id)],
    #                         limit=1).price
    #                     rec.price_unit = price
    #                     self.env['product.subscription.pricing'].search(
    #                         [('period_id', '=', rec.order_id.recurrance_id.id)])
    #                     self.env['product.subscription.pricing'].search([('product_id', '=', rec.product_id.id)])


class ResPartner(models.Model):
    _inherit = "res.partner"

    contract_ids = fields.One2many('sale.order', 'partner_id', string='Contracts')
    contract_count = fields.Integer(compute='_compute_contract_count', string='Contract Count')

    @api.depends('contract_ids.sale_type')
    def _compute_contract_count(self):
        for partner in self:
            partner.contract_count = len(
                partner.contract_ids.filtered(lambda o: o.sale_type == 'contract')
            )

    # def view_contracts(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': "Contracts",
    #         'view_mode': 'tree,form',
    #         'res_model': 'sale.order',
    #         'context': {'create': False},
    #         'domain': [('partner_id', '=', self.id),
    #                    ('sale_type', '=', 'contract')]
    #     }

    def view_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Contracts",
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'context': {'create': False, 'group_by': 'project_type'},
            'domain': [('partner_id', '=', self.id),
                       ('sale_type', '=', 'contract')]
        }

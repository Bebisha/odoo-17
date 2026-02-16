# -*- coding: utf-8 -*-
from itertools import groupby

from odoo import models, fields, api, Command
from odoo.exceptions import UserError, AccessError
from odoo.tools import float_is_zero
from odoo.tools.populate import compute


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    branch_ids = fields.Many2many('kg_branch', compute='compute_branch_ids')


    @api.depends('order_line')
    def compute_branch_ids(self):
        for rec in self:
            rec.branch_ids = False
            if rec.order_line:
                rec.branch_ids = [(6, 0, self.order_line.mapped('branch_id').mapped('id'))]

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)


    def _create_invoices(self, grouped=False, final=False, date=None, branch_id=None):
        """ Create invoice(s) for the given Sales Order(s), optionally for a specific branch.

        :param bool grouped: if True, invoices are grouped by SO id.
            If False, invoices are grouped by keys returned by :meth:`_get_invoice_grouping_keys`
        :param bool final: if True, refunds will be generated if necessary
        :param date: unused parameter
        :param branch_id: if provided, only create invoices for this branch
        :returns: created invoices
        :rtype: `account.move` recordset
        :raises: UserError if one of the orders has no invoiceable lines.
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        invoice_vals_list = []
        invoice_item_sequence = 0  # Incremental sequencing to keep the lines order on the invoice.
        if self.branch_ids:
            for order in self:

                order = order.with_company(order.company_id).with_context(lang=order.partner_invoice_id.lang)
                # Get invoiceable lines
                invoiceable_lines = order._get_invoiceable_lines(final)

                if not invoiceable_lines:
                    raise UserError("No invoiceable lines found for this order.")

                # Group invoiceable lines by branch
                lines_grouped_by_branch = {}
                for line in invoiceable_lines:
                    branch = line.branch_id
                    if branch not in lines_grouped_by_branch:
                        lines_grouped_by_branch[branch] = []
                    lines_grouped_by_branch[branch].append(line)

                # Debug: Print out grouped lines by branch
                # _logger.info(f"Grouped lines by branch: {lines_grouped_by_branch}")
                print(lines_grouped_by_branch,'lines_grouped_by_branch')
                # Ensure each branch gets its own invoice
                for branch, lines in lines_grouped_by_branch.items():
                    # If a specific branch_id is provided, skip other branches
                    if branch_id and branch_id != branch.id:
                        continue

                    # Ensure there are invoiceable lines (non-display type) for the branch
                    if not any(not line.display_type for line in lines):
                        continue

                    # Prepare invoice for this branch
                    invoice_vals = order._prepare_invoice()
                    invoice_vals['branch_id'] = branch.id  # Set the branch on the invoice

                    # Prepare invoice lines
                    invoice_line_vals = []
                    down_payment_section_added = False

                    for line in lines:
                        # Add down payment section if applicable
                        if not down_payment_section_added and line.is_downpayment:
                            invoice_line_vals.append(
                                Command.create(
                                    order._prepare_down_payment_section_line(sequence=invoice_item_sequence)
                                ),
                            )
                            down_payment_section_added = True
                            invoice_item_sequence += 1

                        # Add line to the invoice
                        invoice_line_vals.append(
                            Command.create(
                                line._prepare_invoice_line(sequence=invoice_item_sequence)
                            ),
                        )
                        invoice_item_sequence += 1

                    # Add lines to the invoice and append to the invoice list
                    invoice_vals['invoice_line_ids'] = invoice_line_vals
                    invoice_vals_list.append(invoice_vals)

            # Debug: Ensure we have correct number of invoice vals
            # _logger.info(f"Total invoice vals to create: {len(invoice_vals_list)}")
            print(len(invoice_vals_list),'dddsdfsdfsdfsdfsdfdd')
            # Raise an error if no invoiceable lines are found
            if not invoice_vals_list and self._context.get('raise_if_nothing_to_invoice', True):
                raise UserError(self._nothing_to_invoice_error_message())

            # Create invoices (no grouping applied, each branch gets a separate invoice)
            moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

            # Handle refunds if final=True
            if final:
                moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_move_type()

            # Post a message on each invoice
            for move in moves:
                move.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': move, 'origin': move.line_ids.sale_line_ids.order_id},
                    subtype_xmlid='mail.mt_note',
                )

            return moves
        else:
            return super(SaleOrder, self)._create_invoices()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # branch_id = fields.Many2one('kg_branch')

    branch_id = fields.Many2one('kg_branch', string="Branch", compute='_compute_branch_id', store=True, readonly=True)

    @api.depends('product_id')
    def _compute_branch_id(self):
        for line in self:
            # Set branch_id based on product's branch_id
            line.branch_id = line.product_id.product_tmpl_id.branch_id if line.product_id else False

    def _prepare_invoice_line(self, **optional_values):
        invoice_line = super()._prepare_invoice_line(**optional_values)
        invoice_line['branch_id'] = self.branch_id.id
        return invoice_line

class StockCustoms(models.Model):
    _inherit = 'stock.move'
    _description = 'stock customizations'

    branch_id = fields.Many2one('kg_branch', string="Branch")
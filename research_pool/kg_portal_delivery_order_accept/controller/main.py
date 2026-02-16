from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager,_
import base64



class PortalEvent(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        values['vendor_count'] = request.env['stock.picking'].search_count([])
        return values

    @http.route(["/my/delivery/order", "/my/delivery/order/page/<int:page>"], type='http', auth='user', website=True)
    def vendor_lists_views(self, page=1, sortby='name', search="", search_in="all", **kw):
        sort_list = {
            'name': {'label': _('Reference'), 'order': 'name asc, id asc'},
            'date': {'label': _('Scheduled Date'), 'order': 'scheduled_date asc, id asc'},
            'deadline': {'label': _('Deadline'), 'order': 'date_deadline asc, id asc'},
            'state': {'label': _('State'), 'order': 'state asc, id asc'}
        }
        default_order_by = sort_list.get(sortby, {}).get('Reference', 'name asc, id asc')

        search_list = {
            'state': {'label': 'State', 'input': 'state',
                      'domain': [('state', '=', search), ('picking_type_code', '=', 'outgoing')]},
        }
        search_domain = search_list.get(search_in, {}).get('domain', [('picking_type_code', '=', 'outgoing'),('warehouse_id', '=', request.env.user.property_warehouse_id.id),('state', '=', 'assigned')])


        picking_list = request.env['stock.picking']
        picking_total = picking_list.search_count(search_domain)
        pager_details = pager(url="/my/delivery/order", total=picking_total, page=page,
                              url_args={'sortby': sortby, 'search_in': search_in, 'search': search}, step=10)
        pickings = picking_list.search(search_domain, limit=10, order=default_order_by, offset=pager_details['offset'])
        # print(pickings['state'],'pickings')
        state_selection = dict(picking_list.fields_get(allfields=['state'])['state']['selection'])
        keys = list(state_selection.keys())
        values = list(state_selection.values())
        vals = {
            'pickings': pickings,
            'keys': keys,
            'values': values,
            'page_name': 'my_delivery_list_views', 'pager': pager_details, 'sortby': sortby,
            'searchbar_sortings': sort_list, 'search_in': search_in,
            'search': search,

        }
        # print(vals)

        return request.render("kg_portal_delivery_order_accept.my_delivery_list_views", vals)








    @http.route("/my/delivery/order/accept/<int:picking_id>", type='http', auth='user', website=True)
    def create_invoice(self, picking_id=None):
        delivery_order = request.env['stock.picking'].browse(picking_id)

        # Check if the delivery order exists
        if not delivery_order:
            return "Delivery order not found!"

        # Check if the delivery order is in the "assigned" state
        if delivery_order.state != 'assigned':
            return "Delivery order is not in the 'assigned' state. Cannot create invoice."

        # Confirm the delivery order if it's not already confirmed
        if delivery_order.state != 'done':
            delivery_order.action_confirm()

        invoice_line_vals = []
        if delivery_order.sale_id:
            for line in delivery_order.move_ids_without_package:
                if line.product_id:
                    invoice_line_vals.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'quantity': line.product_qty,
                        'price_unit': line.product_id.list_price,
                        'sale_line_ids': [(6, 0, [sale_line.id]) for sale_line in delivery_order.sale_id.order_line],
                    }))
        else:
            for line in delivery_order.move_ids_without_package:
                if line.product_id:
                    invoice_line_vals.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'quantity': line.product_qty,
                        'price_unit': line.product_id.list_price,
                    }))

        invoice_vals = {
            'invoice_origin': delivery_order.name,
            'move_type': 'out_invoice',
            'partner_id': delivery_order.partner_id.id,
            'invoice_line_ids': invoice_line_vals,
        }

        invoice = request.env['account.move'].create(invoice_vals)
        delivery_order.boolean = True

        return request.redirect("/my/delivery/order")






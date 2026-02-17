from odoo import http
from odoo.http import request


class KGCustomPurchaseEntryPortal(http.Controller):

    @http.route(['/purchase/order/<int:order_id>'], type='http', auth='public', website=True)
    def purchase_order_view(self, order_id, **kwargs):
        order = request.env['purchase.entry'].sudo().browse(order_id)
        if not order.exists():
            return request.not_found()
        return request.render('kg_raw_fisheries_purchase.kg_custom_purchase_order_template', {
            'order': order
        })

    @http.route(['/purchase/order/approve/<int:order_id>'], type='http', auth='public', website=True)
    def approve_purchase(self, order_id, **kwargs):
        order = request.env['purchase.entry'].sudo().browse(order_id)
        if order.exists():
            if order.state == 'approved':
                return self._popup_response('Already Approved')
            if order.state == 'rejected':
                return self._popup_response('This record has already been rejected.')
            if order.state == 'confirm':
                order.action_approve()
            if order.state in ['draft', 'cancel']:
                return self._popup_response('Cannot approve a draft or cancelled order.')
        return self._popup_response('Approved successfully!')


    @http.route(['/purchase/order/reject/<int:order_id>'], type='http', auth='public', website=True, methods=['POST'])
    def reject_purchase(self, order_id, **kw):
        order = request.env['purchase.entry'].sudo().browse(order_id)
        if not order.exists():
            return request.redirect('/')
        reason = kw.get('update_reason')
        order.write({'state': 'rejected', 'reject_reason': reason})
        return request.redirect('/purchase/order/%s' % order_id)

    @staticmethod
    def _popup_response(message):
        return f"""
            <html>
                <head>
                    <script>
                        alert('{message}');
                        window.location.href = document.referrer;
                    </script>
                </head>
                <body></body>
            </html>
        """


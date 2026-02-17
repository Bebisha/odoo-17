from odoo import http
from odoo.http import request


class KGApprovalController(http.Controller):

    @http.route('/web/action_approve', type='http', auth="user", csrf=False)
    def action_approve(self, id, **kwargs):
        record = request.env['account.move'].sudo().browse(int(id))
        if record:
            if record.state == 'rejected':
                return self._popup_response('This record has already been rejected.')
            if record.need_final_approve:
                if record.waiting_final_approve:
                    return self._popup_response('Already Approved')
            else:
                if record.state != 'approval_requested':
                    return self._popup_response('Already Approved')

            approver_id = record.bill_approve_user_id.id if record.move_type == 'in_invoice' else record.inv_approve_user_id.id

            if request.env.user.id != approver_id:
                return self._popup_response('You have no access to approve!')

            record.action_approve()
            return self._popup_response('Approved successfully!')

    @http.route('/web/action_final_approve', type='http', auth="user", csrf=False)
    def action_final_approve(self, id, **kwargs):
        record = request.env['account.move'].sudo().browse(int(id))
        if record:
            if record.state == 'rejected':
                return self._popup_response('This record has already been rejected.')
            if record.need_final_approve:
                if record.state != 'approval_requested':
                    return self._popup_response('Already Approved')

            approver_id = record.bill_final_approve_user_id.id if record.move_type == 'in_invoice' else record.inv_final_approve_user_id.id

            if request.env.user.id != approver_id:
                return self._popup_response('You have no access to approve!')

            record.action_final_approve()
            return self._popup_response('Approved successfully!')

    @staticmethod
    def _popup_response(message):
        return f"""
            <html>
                <head>
                    <script>
                        alert('{message}');
                        window.close();
                    </script>
                </head>
                <body></body>
            </html>
        """

    @http.route('/thank-you-template', type='http', auth='user', website=True)
    def render_thank_you_template(self, **kwargs):
        return request.render('kg_raw_fisheries_accounting.thank_you_template', {})

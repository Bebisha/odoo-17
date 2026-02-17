from odoo import http
from odoo.http import request


class ApprovalController(http.Controller):
    @http.route('/web/action_first_approve', type='http', auth="user", csrf=False)
    def action_first_approve(self, id, **kwargs):
        record = request.env['kg.batch.expense'].sudo().browse(int(id))
        if record:
            if record.state == 'draft':
                record.action_first_approve()

                return """
                <html>
                    <head>
                        <script>
                            alert('Approved successfully!');
                            window.close();
                        </script>
                    </head>
                    <body>
                    </body>
                </html>
                """
            else:
                return """
                                <html>
                                    <head>
                                        <script>
                                            alert('Already Approved');
                                            window.close();
                                        </script>
                                    </head>
                                    <body>
                                    </body>
                                </html>
                                """

    @http.route('/web/action_reject', type='http', auth="user", csrf=False)
    def action_reject(self, id, **kwargs):
        record = request.env['kg.batch.expense'].sudo().browse(int(id))
        print(record, 'record')

        if record:
            if record.state in ['draft','1st_approve']:
                record.sudo().action_reject()
                return """
                        <html>
                            <head>
                                <script>
                                    alert('Request Rejected!');
                                    window.close();
                                </script>
                            </head>
                            <body>
                            </body>
                        </html>
                        """
            else:
                return """
                        <html>
                            <head>
                                <script>
                                    alert('Already Rejected');
                                    window.close();
                                </script>
                            </head>
                            <body>
                            </body>
                        </html>
                        """

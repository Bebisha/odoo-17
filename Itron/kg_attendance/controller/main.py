from odoo import http
from odoo.http import request


class ApprovalController(http.Controller):
    @http.route('/web/action_first_approval', type='http', auth="user", csrf=False)
    def action_first_approval(self, id, **kwargs):
        record = request.env['early.late.request'].sudo().browse(int(id))
        if record:
            if record.state == 'request':
                record.action_first_approval()

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

    @http.route('/web/action_second_approval', type='http', auth="user", csrf=False)
    def action_second_approval(self, id, **kwargs):
        record = request.env['early.late.request'].sudo().browse(int(id))
        if record:
            if record.state == 'lm_approved':
                record.action_second_approval()

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

    # @http.route('/web/action_reject', type='http', auth="user", csrf=False)
    # def action_reject(self, id, **kwargs):
    #     record = request.env['early.late.request'].sudo().browse(int(id))
    #     if record:
    #         if record.state in ['cancel']:
    #             return """
    #                     <html>
    #                         <head>
    #                             <script>
    #                                 alert('Already Rejected!');
    #                                 window.close();
    #                             </script>
    #                         </head>
    #                         <body>
    #                         </body>
    #                     </html>
    #                     """
    #         elif record.state not in ['lm_approved']:
    #             record.action_reject()
    #             return """
    #                     <html>
    #                         <head>
    #                             <script>
    #                                 alert('Request Rejected');
    #                                 window.close();
    #                             </script>
    #                         </head>
    #                         <body>
    #                         </body>
    #                     </html>
    #                     """
    #         else:
    #             return """
    #                     <html>
    #                         <head>
    #                             <script>
    #                                 alert('Already Approved');
    #                                 window.close();
    #                             </script>
    #                         </head>
    #                         <body>
    #                         </body>
    #                     </html>
    #                     """

    @http.route('/thank-you-template', type='http', auth='user', website=True)
    def render_thank_you_template(self, **kwargs):
        return request.render('kg_attendance.thank_you_template', {})


import requests
from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
import json

class SessionInherits(http.Controller):

    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        credential = {'login': login, 'password': password, }
        print(credential, "credential")
        pre_uid = request.session.authenticate(db, login, password)
        print(pre_uid,'pre_uid')
        return request.env['ir.http'].session_info()

    # @http.route('/register', methods=['POST'], type='json', auth="user")
    # def registers(self, **post):
    #     payment_id = post.get("id")
    #
    #     # Get payment record
    #     payment = request.env['account.payment'].sudo().browse(int(payment_id))
    #     if not payment.exists():
    #         return {"error": f"Payment record with ID {payment_id} does not exist"}
    #
    #     created_user = payment.create_uid
    #     current_user = payment.create_uid.name
    #     created_user_email = payment.create_uid.email
    #     company_name = created_user.company_id.name if created_user.company_id else "No Company"
    #     user_password = created_user.plain_password or "defaultpassword"
    #
    #     quota = ""
    #     transaction = payment.payment_transaction_id
    #     if transaction and transaction.sale_order_ids:
    #         order_lines = transaction.sale_order_ids.mapped('order_line')
    #         if order_lines:
    #             product = order_lines[0].product_id
    #             attr_val = product.product_template_attribute_value_ids[:1]
    #             if attr_val:
    #                 quota = int(attr_val.name)
    #     else:
    #         invoices = payment.reconciled_invoice_ids
    #         invoice_lines = invoices.mapped('invoice_line_ids')
    #         if invoice_lines:
    #             product = invoice_lines[0].product_id
    #             attr_val = product.product_template_attribute_value_ids[:1]
    #             if attr_val:
    #                 quota = int(attr_val.name)
    #
    #     data_to_send = {
    #         "companyName": 'Test1',
    #         "adminName": current_user,
    #         "email": created_user_email,
    #         "password": user_password,
    #         "confirmPassword": user_password,
    #         "quota": quota or 1000
    #     }
    #     print(data_to_send,"data_to_send")
    #
    #     base_url = request.env['ir.config_parameter'].sudo().get_param('external_api.base_url')
    #     print(base_url,"base_url")
    #     if not base_url:
    #         return {"status": "error", "message": "External API base URL not configured in System Parameters."}
    #     headers_1 = {"Content-Type": "application/json"}
    #     full_url = f"{base_url}/api/auth/register"
    #     print(full_url,"full_url")
    #     try:
    #         response = requests.post(full_url, json=data_to_send, headers=headers_1, timeout=30)
    #         try:
    #             return response.json()
    #         except Exception:
    #             return {"status": "error", "raw_response": response.text}
    #
    #     except requests.exceptions.RequestException as e:
    #         return {
    #             "status": "error",
    #             "message": str(e),
    #             "raw_response": getattr(e.response, "text", None),
    #         }

    @http.route('/register', methods=['POST'], type='json', auth="user")
    def registers(self, **post):
        payment_id = post.get("id")

        # Validate payment record
        payment = request.env['account.payment'].sudo().browse(int(payment_id))
        if not payment.exists():
            return {"error": f"Payment record with ID {payment_id} does not exist"}

        created_user = payment.create_uid
        current_user = created_user.name
        created_user_email = created_user.email
        company_name = created_user.company_id.name if created_user.company_id else "No Company"
        user_password = created_user.plain_password or "defaultpassword"

        # -----------------------
        # Extract quota
        # -----------------------
        quota = 0
        transaction = payment.payment_transaction_id

        # From Sale Order
        if transaction and transaction.sale_order_ids:
            order_lines = transaction.sale_order_ids.mapped('order_line')
            if order_lines:
                product = order_lines[0].product_id
                attr_val = product.product_template_attribute_value_ids[:1]
                if attr_val:
                    quota = int(attr_val.name)

        # From Invoice
        else:
            invoices = payment.reconciled_invoice_ids
            invoice_lines = invoices.mapped('invoice_line_ids')
            if invoice_lines:
                product = invoice_lines[0].product_id
                attr_val = product.product_template_attribute_value_ids[:1]
                if attr_val:
                    quota = int(attr_val.name)

        # -----------------------
        # Prepare payload
        # -----------------------
        data_to_send = {
            "companyName": company_name,
            "adminName": current_user,
            "email": created_user_email,
            "password": user_password,
            "confirmPassword": user_password,
            "quota": quota or 1000
        }

        # Read external API base URL
        base_url = request.env['ir.config_parameter'].sudo().get_param('external_api.base_url')
        if not base_url:
            return {
                "status": "error",
                "message": "External API base URL not configured in System Parameters."
            }

        full_url = f"{base_url}/api/auth/register"
        headers = {"Content-Type": "application/json"}

        # -----------------------
        # Send to external API
        # -----------------------
        try:
            response = requests.post(full_url, json=data_to_send, headers=headers, timeout=30)

            # Parse JSON if possible
            try:
                api_response = response.json()
            except Exception:
                return {"status": "error", "raw_response": response.text}

            # -----------------------
            # Update Odoo user quota if success
            # -----------------------
            if api_response.get("status") == "success":
                total_limit = api_response.get("totalQuoteLimit")
                if total_limit:
                    created_user.sudo().write({
                        'total_quote_limit': float(total_limit)
                    })

            return api_response

        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": str(e),
                "raw_response": getattr(e.response, "text", None),
            }

    @http.route('/quote/update', methods=['POST'], type='json', auth="user")
    def quote_update(self, **post):

        sale_id = post.get("sale_id")
        action = post.get("action")  # deduct / refund / adjust
        amount = post.get("amount")

        if not sale_id:
            return {"status": "error", "message": "Sale Order ID missing"}

        sale = request.env['sale.order'].sudo().browse(int(sale_id))
        if not sale.exists():
            return {"status": "error", "message": f"Sale Order {sale_id} not found"}

        user = sale.user_id
        company = sale.company_id.name if sale.company_id else "No Company"

        data_to_send = {
            "user_id": user.id,
            "user_name": user.name,
            "email": user.email or "",
            "quotation": sale.name,
            "action": action,
            "amount": amount,
            "company": company,
        }

        print(data_to_send, "QUOTE API DATA")

        base_url = request.env['ir.config_parameter'].sudo().get_param(
            'external_api.base_url'
        )

        if not base_url:
            return {
                "status": "error",
                "message": "External API base URL not configured"
            }

        headers_1 = {"Content-Type": "application/json"}
        full_url = f"{base_url}/api/quote/update"

        try:
            response = requests.post(
                full_url,
                json=data_to_send,
                headers=headers_1,
                timeout=30
            )

            try:
                return response.json()
            except Exception:
                return {
                    "status": "error",
                    "raw_response": response.text
                }

        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": str(e),
                "raw_response": getattr(e.response, "text", None)
            }


class AuthSignupHomeInherits(AuthSignupHome):

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        password = kw.get("password")

        response = super(AuthSignupHomeInherits, self).web_auth_signup(*args, **kw)

        if password and kw.get("login"):
            user = request.env["res.users"].sudo().search(
                [("login", "=", kw["login"])], limit=1
            )
            if user:
                user.sudo().write({"plain_password": password})

        return response
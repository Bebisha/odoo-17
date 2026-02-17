from odoo import http
from odoo.http import request
from werkzeug.utils import redirect

class UpdateRFQController(http.Controller):

    @http.route(['/my/po/<int:order_id>/update_all'], type='http', auth="public", methods=['POST'])
    def update_all(self, order_id, **kw):

        price_unit_key_prefix = 'price_unit_'
        price_unit_data = {}
        new_receipt_date = kw.get('new_receipt_date')
        user_id = request.env.user

        price_changed = False
        receipt_date_changed = False
        changed_products = []

        for key, value in kw.items():
            if key.startswith(price_unit_key_prefix):
                try:
                    line_id = int(key[len(price_unit_key_prefix):])
                    price_unit = float(value)
                    price_unit_data[line_id] = price_unit
                except ValueError:
                    continue

        purchase_order = request.env['purchase.order'].sudo().browse(order_id)

        for line_id, price_unit in price_unit_data.items():
            order_line = request.env['purchase.order.line'].sudo().browse(line_id)
            if order_line and order_line.price_unit != price_unit:
                order_line.write({'price_unit': price_unit})
                price_changed = True
                changed_products.append(order_line)

        if new_receipt_date and purchase_order.date_planned != new_receipt_date:
            purchase_order.write({'date_planned': new_receipt_date})
            receipt_date_changed = True

        log_note_content = []

        if receipt_date_changed:
            log_note_content.append(f"Receipt Date updated to: {new_receipt_date}")

        if price_changed:
            price_updates = "Prices updated: " + ", ".join(
                [f"Product: {line.product_id.name}, New Price: {price_unit_data[line.id]}" for line in changed_products]
            )
            log_note_content.append(price_updates)

        if not price_changed and not receipt_date_changed:
            return redirect(request.httprequest.referrer)

        email_subject = f"Purchase Order Update: {purchase_order.name}"
        vendor_name = purchase_order.partner_id.name
        email_body = f"""
           <p>Dear {user_id.name},</p>
           <p>The following changes have been made to the Request for Quotation {purchase_order.name} for vendor: <strong>{vendor_name}</strong></p>
           """

        if receipt_date_changed:
            email_body += f"<h3>Updated Delivery Date</h3><p>{new_receipt_date}</p>"

        if price_changed:
            email_body += "<h3>Updated Price List</h3><ul>"
            for line in changed_products:
                email_body += f"<li>Product: {line.product_id.name}, New Price: {price_unit_data[line.id]}</li>"
            email_body += "</ul>"

        email_body += "<p>Thank you.</p>"

        mail_values = {
            'subject': email_subject,
            'body_html': email_body,
            'email_to': user_id.email,
            'email_from': request.env.user.email,
        }

        mail = request.env['mail.mail'].create(mail_values)
        mail.send()

        log_note_content.append(f"Notification email sent to {user_id.name} ({user_id.email})")

        log_note_content_str = ", ".join(log_note_content)

        if log_note_content_str:
            purchase_order.message_post(
                body=log_note_content_str.strip(),
                subtype_id=request.env.ref('mail.mt_note').id
            )

        return redirect(request.httprequest.referrer)
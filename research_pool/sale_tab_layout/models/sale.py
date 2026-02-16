from odoo import api, fields, models
import base64


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    aircraft_name = fields.Char(string="Aircraft Name")
    image_main = fields.Image("Main Image")
    image_layout = fields.Image("Layout Image")
    image_interior = fields.Image("Interior Image")
    year_of_manufacture = fields.Char(string="YOM")
    refurbished = fields.Char(string="Refurbished")
    seats = fields.Integer(string="Seats")
    wifi = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="WiFi")
    smoking = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Smoking")
    remarks = fields.Text(string="Remarks")



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    aircraft_preview = fields.Html(string="Aircraft Preview", compute="_compute_aircraft_preview", sanitize=False)
    image_main = fields.Image("Main Image")
    image_layout = fields.Image("Layout Image")
    image_interior = fields.Image("Interior Image")

    @api.depends('product_id')
    def _compute_aircraft_preview(self):
        for line in self:
            tmpl = line.product_id.product_tmpl_id

            def render_image(image):
                if image:
                    try:
                        if isinstance(image, bytes):
                            image = base64.b64encode(image).decode('utf-8')
                        elif isinstance(image, str) and not image.startswith('data:image/png;base64,'):
                            image = image.strip()
                        return f'<img src="data:image/png;base64,{image}" style="width: 100%; height: 100pt; object-fit: cover;" />'
                    except Exception as e:
                        print(f"Error rendering image: {e}")
                        return ''
                return ''

            image_main = render_image(tmpl.image_main)
            image_layout = render_image(tmpl.image_layout)
            image_interior = render_image(tmpl.image_interior)
            specs = f"""
                <p><strong>YOM:</strong> {tmpl.year_of_manufacture or 'N/A'}</p>
                <p><strong>Refurbished:</strong> {tmpl.refurbished or 'N/A'}</p>
                <p><strong>Seats:</strong> {tmpl.seats or 'N/A'}</p>
                <p><strong>WiFi:</strong> {tmpl.wifi or 'No'}</p>
                <p><strong>Smoking:</strong> {tmpl.smoking or 'No'}</p>
                <p><strong>Remarks:</strong> {tmpl.remarks or ''}</p>
            """
            line.aircraft_preview = f"""
                <div style="width:100%; display:flex;">
                    <div style="width:33%; padding:5px; vertical-align:top;">{specs}</div>
                </div>
            """

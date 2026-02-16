from odoo import models, fields
from bs4 import BeautifulSoup


class AddSectionWizard(models.TransientModel):
    _name = "add.section.wizard"
    _description = "Add a Section"

    name = fields.Char(string="Reference")
    sale_id = fields.Many2one("sale.order", string="SO")
    description = fields.Html(string="Description")

    def add_section(self):
        if self.description:
            description = BeautifulSoup(self.description, "html.parser")
            print(description,"description")
            lines = description.get_text(separator="\n").split("\n")
            print(lines,"lines")
            combined_lines = "\n".join(lines)

            val = {'name': combined_lines,
                'display_type': 'line_section',
                'order_id': self.sale_id.id,
                'kg_description': self.description
             }
            print(val,"val")

            self.env['sale.order.line'].create(val)


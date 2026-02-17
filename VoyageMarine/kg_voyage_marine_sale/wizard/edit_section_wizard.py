from odoo import models, fields, api
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from odoo.exceptions import ValidationError


class EditSectionWizard(models.TransientModel):
    _name = "edit.section.wizard"
    _description = "Edit a Section"

    name = fields.Char(string="Reference")
    sale_id = fields.Many2one("sale.order", string="SO")
    sol_ids = fields.Many2many("sale.order.line", string="Select Section",
                               domain=[('display_type', '=', 'line_section')])
    sol_id = fields.Many2one("sale.order.line", string="Select Section", domain="[('id','in',sol_ids)]")
    description = fields.Html(string="Description")

    @api.onchange('sol_id')
    def show_description(self):
        for rec in self:
            if rec.sol_id and rec.sol_id.kg_description:
                rec.description = rec.sol_id.kg_description
            else:
                rec.description = False

    def _html_to_ui_text(self, html):
        soup = BeautifulSoup(html, "html.parser")
        output = []

        for element in soup.contents:

            # 1️⃣ PURE TEXT (VERY IMPORTANT)
            if isinstance(element, NavigableString):
                text = element.strip()
                if text:
                    output.append(text)

            # 2️⃣ ORDERED LIST
            elif element.name == "ol":
                for idx, li in enumerate(element.find_all("li", recursive=False), 1):
                    text = li.get_text(strip=True)
                    if text:
                        output.append(f"{idx}. {text}")

            # 3️⃣ UNORDERED LIST / CHECKLIST
            elif element.name == "ul":
                for li in element.find_all("li", recursive=False):
                    checkbox = li.find("input", {"type": "checkbox"})
                    text = li.get_text(strip=True)

                    if checkbox:
                        checked = checkbox.has_attr("checked")
                        symbol = "☑" if checked else "☐"
                        output.append(f"{symbol} {text}")
                    else:
                        output.append(f"• {text}")

            # 4️⃣ TABLE
            elif element.name == "table":
                for row in element.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                    output.append(" | ".join(cells))

            # 5️⃣ PARAGRAPH
            elif element.name == "p":
                text = element.get_text(strip=True)
                if text:
                    output.append(text)

        return "\n".join(output)

    def edit_section(self):
        if not self.description or self.description == '<p><br></p>':
            raise ValidationError("Description is missing !!")

        combined_lines = self._html_to_ui_text(self.description)

        self.sol_id.write({
            "name": combined_lines,  # UI
            "kg_description": self.description,  # PDF
        })

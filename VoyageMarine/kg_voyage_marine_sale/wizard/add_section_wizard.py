from odoo import models, fields
from bs4 import BeautifulSoup


class AddSectionWizard(models.TransientModel):
    _name = "add.section.wizard"
    _description = "Add a Section"

    name = fields.Char(string="Reference")
    sale_id = fields.Many2one("sale.order", string="SO")
    description = fields.Html(string="Description")

    def add_section(self):
        if not self.description:
            return

        soup = BeautifulSoup(self.description, "html.parser")
        output = []

        # Iterate over top-level elements only
        for element in soup.contents:

            # ORDERED LIST
            if element.name == "ol":
                for idx, li in enumerate(element.find_all("li", recursive=False), 1):
                    output.append(f"{idx}. {li.get_text(strip=True)}")

            # UNORDERED LIST / CHECKLIST
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

            # TABLE
            elif element.name == "table":
                for row in element.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                    output.append(" | ".join(cells))

            # PARAGRAPH
            elif element.name == "p":
                text = element.get_text(strip=True)
                if text:
                    output.append(text)

            # PURE TEXT (very important)
            elif isinstance(element, str):
                text = element.strip()
                if text:
                    output.append(text)

        combined_lines = "\n".join(output)

        self.env["sale.order.line"].create({
            "name": combined_lines,  # UI
            "display_type": "line_section",
            "order_id": self.sale_id.id,
            "kg_description": self.description,  # PDF
        })



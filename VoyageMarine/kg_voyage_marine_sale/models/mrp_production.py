from odoo import models, fields,api,_

class KGMRProductionIherit(models.Model):
    _inherit = "mrp.production"

    sale_id = fields.Many2one("sale.order", string="SO")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('mr.seq') or '/'
        return super(KGMRProductionIherit, self).create(vals)

    def action_generate_bom(self):
        """ Generates a new Bill of Material based on the Manufacturing Order's product, components,
        workorders and by-products, and assigns it to the MO. Returns a new BoM's form view action.
        """
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('mrp.mrp_bom_form_action')
        action['view_mode'] = 'form'
        action['views'] = [(False, 'form')]
        action['target'] = 'new'

        bom_lines_vals, byproduct_vals, operations_vals = self._get_bom_values()
        action['context'] = {
            'default_bom_line_ids': bom_lines_vals,
            'default_byproduct_ids': byproduct_vals,
            'default_company_id': self.company_id.id,
            'default_operation_ids': operations_vals,
            'default_product_id': self.product_id.id,
            'default_product_qty': self.product_qty,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id,
            'default_product_uom_id': self.product_uom_id.id,
            'parent_production_id': self.id,  # Used to assign the new BoM to the current MO.
        }
        return action


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'),('ft','FT')
    ], string="Code")

    unit_price = fields.Float(string='Unit Price')





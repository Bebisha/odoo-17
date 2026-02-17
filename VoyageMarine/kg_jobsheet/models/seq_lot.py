from datetime import date

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

class KGSequence(models.Model):
    _inherit = "sequence.lot"
    _description = "Lot Sequence"

    calibration_id = fields.Many2one('calibration.form', string="Calibration")
    # seq_line_lot = fields.Many2one('calibration.form', string="Calibration")




class KSequenceLine(models.Model):
    _name = "sequence.lot.line"
    _description = "Lot Sequence"

    x_check_done = fields.Boolean(string="Done?" ,copy=False)
    is_already_created = fields.Boolean(string="IS Created" ,copy=False)
    name = fields.Char(string="Sequence Number",)
    pro_id = fields.Many2one('product.product', string="Product", domain="[('detailed_type','=','product')]")
    product_temp_id = fields.Many2one('product.template', string="Product Template")
    make = fields.Char(string="Make", )
    serial_no = fields.Char(string="Serial number", )
    make_id = fields.Many2one('rec.make', string='Make')
    model_id = fields.Many2one('rec.model', string='Model')
    model = fields.Char(string='Model', )
    uom_id = fields.Many2one('uom.uom', related='pro_id.uom_id', string='UOM')
    # price = fields.Float('Price', required=True)
    unit_price = fields.Float(string='Unit Price')
    product_category = fields.Many2one('product.category', string="Category", related='pro_id.categ_id')
    description = fields.Text(string='Description')
    des = fields.Char(string='Description')
    physical_status_id = fields.Many2one('physical.status', string="Physical Status")
    accesories = fields.Text(string="Accessories")
    qty = fields.Float(string="Quantity", default=1.00)
    remark = fields.Text(string='Remark', copy=False)
    lot_number_text = fields.Text(string='Serial Numbers')
    lot_ids = fields.Many2many('stock.lot', string='Assigned Serials')
    lot_id = fields.Many2one('stock.lot', string='Assigned Serials')
    seq_line_lot = fields.Many2one('calibration.form', string="Calibration")
    ffa_form_lot = fields.Many2one('ffa.form', string="FFA")
    field_serv_lot = fields.Many2one('field.service', string="Field Service")
    lsa_lot = fields.Many2one('lsa.form', string="LSA")
    nav_com_lot = fields.Many2one('navigation.communication', string="Navigation Communication")
    lead_id = fields.Many2one('crm.lead', string="Lead")


class KGstockingPicking(models.Model):
    _inherit = "stock.picking"

    repair_id = fields.Many2one('repair.order', string="Repair")






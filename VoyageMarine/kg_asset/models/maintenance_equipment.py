from odoo import models, fields,api

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'
    _rec_name = 'display_name'

    @api.depends('name', 'asset_code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.asset_code:
                rec.display_name = f"{rec.name}({rec.asset_code})"

    vehicle_no = fields.Char(string="Vehicle No")
    engine_no = fields.Char(string="Engine No")
    pocession = fields.Char(string="Pocession")
    make = fields.Char(string='Make')

    inspection_date = fields.Char(string='Inspection Date/Inspected By')
    certificate_no = fields.Char(string='Certificate No.')
    cal_date = fields.Date(string='Cal Date')
    due_date = fields.Date(string='Due Date')
    asset_model_code = fields.Many2one('account.asset',string="Asset Model Code", help="Unique code for the asset.")
    asset_code = fields.Char(related="asset_model_code.sequence_number",string="Asset Code")

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.technician_user_id:
            self.technician_user_id = self.category_id.technician_user_id

    @api.onchange('asset_model_code')
    def _onchange_asset_model_code(self):
        """When Asset Model Code changes, auto-fill matching values."""
        if self.asset_model_code:
            asset = self.asset_model_code

            # Copy values if available in the asset record
            self.vehicle_no = asset.vehicle_no or False
            self.engine_no = asset.engine_no or False
            self.pocession = asset.pocession or False
            self.serial_no = asset.serial_no or False
            self.model = asset.model or False
            self.make = asset.make or False
            self.inspection_date = asset.inspection_date or False
            self.certificate_no = asset.certificate_no or False
            self.cal_date = asset.cal_date or False
            self.due_date = asset.due_date or False


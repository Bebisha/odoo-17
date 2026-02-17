from odoo import models, fields,api

class AccountAsset(models.Model):
    _inherit = 'account.asset'
    _rec_name = 'display_name'

    @api.depends('name', 'sequence_number')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.sequence_number:
                rec.display_name = f"{rec.name}({rec.sequence_number})"

    display_name = fields.Char(compute='_compute_display_name')


    asset_model_code = fields.Char(string="Asset Model Code", required=True, help="Unique code for the asset.")
    sequence_number = fields.Char(string="Sequence Number", compute="_compute_sequence_number", store=True)
    vehicle_no = fields.Char(string="Vehicle No")
    engine_no = fields.Char(string="Engine No")
    pocession = fields.Char(string="Pocession")
    category_id = fields.Many2one('product.category', string='Category')
    make = fields.Char(string='Make')
    model = fields.Char(string='Model')
    serial_no = fields.Char(string='Serial No')
    inspection_date = fields.Char(string='Inspection Date/Inspected By')
    certificate_no = fields.Char(string='Certificate No.')
    cal_date = fields.Date(string='Cal Date')
    due_date = fields.Date(string='Due Date')

    _sql_constraints = [('asset_model_code_unique', 'unique(asset_model_code)', 'The sequence number must be unique!')]

    @api.depends('model_id')
    def _compute_sequence_number(self):
        pass

    def _generate_model_sequence(self, model_id):
        if not model_id.asset_model_code:
            return self._generate_default_sequence()
        last_asset = self.env['account.asset'].search([('model_id', '=', model_id.id)], order='create_date desc',
                                                      limit=1)
        new_sequence_number = f"{model_id.asset_model_code}0001"
        if last_asset:
            last_sequence_number = last_asset.sequence_number
            if last_sequence_number:
                sequence_parts = last_sequence_number[len(model_id.asset_model_code):]
                if sequence_parts.isdigit():
                    new_sequence_number = f"{model_id.asset_model_code}{int(sequence_parts) + 1:04d}"

        return new_sequence_number

    def _generate_default_sequence(self):
        return self.env['ir.sequence'].next_by_code('account.asset.sequence')

    @api.model
    def create(self, vals):
        if vals.get('model_id'):
            model_id = self.env['account.asset'].browse(vals['model_id'])
            vals['sequence_number'] = self._generate_model_sequence(model_id)
        else:
            vals['sequence_number'] = self._generate_default_sequence()

        return super(AccountAsset, self).create(vals)

    def write(self, vals):
        if 'model_id' in vals:
            for asset in self:
                if asset.model_id.id != vals['model_id']:
                    new_model = self.env['account.asset'].browse(vals['model_id'])
                    if new_model:
                        vals['sequence_number'] = self._generate_model_sequence(new_model)
                    else:
                        vals['sequence_number'] = self._generate_default_sequence()
        return super(AccountAsset, self).write(vals)
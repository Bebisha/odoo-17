from odoo import models, fields, api, exceptions


class GenerateChequeWizard(models.TransientModel):
    _name = "generate.cheque.wizard"

    journal_id = fields.Many2one('account.journal', string="Journal", domain="[('type', '=', 'bank')]")
    bank_account_id = fields.Many2one('res.bank', string="Bank Account", readonly=True)
    start_series = fields.Integer(string="Start Series", required=True)
    leaf_count = fields.Integer(string="Leaf Count", required=True)
    zero_padding = fields.Integer('Zero Padding Number')
    # cheque_start_series = fields.Integer(string="Cheque Start Series", compute='_compute_cheque_start_series')
    cheque_end_series = fields.Integer(string="Cheque End Series", compute='_compute_cheque_end_series')
    start_seri = fields.Char(string="Start Seri")

    # @api.onchange('start_series', 'zero_padding', 'cheque_end_series')
    # def onchange_zero_padding(self):
    #     zero_padding = self.zero_padding
    #     if self.start_series and zero_padding:
    #         self.start_series = "{:0{}}".format(self.start_series, zero_padding)
    #     # if self.cheque_end_series:
    #     #     self.cheque_end_series = "{:0{}}".format(zero_padding, self.cheque_end_series)

    @api.onchange('journal_id')
    def _on_journal_id_change(self):
        if self.journal_id and self.journal_id.bank_account_id.bank_id:
            self.bank_account_id = self.journal_id.bank_account_id.bank_id.id
        else:
            self.bank_account_id = False

    @api.model
    def create(self, vals):
        if not vals.get('start_series') or not vals.get('leaf_count'):
            raise exceptions.ValidationError("Start Series and Leaf Count are required fields.")
        return super(GenerateChequeWizard, self).create(vals)

    @api.depends('start_series', 'leaf_count')
    def _compute_cheque_end_series(self):
        for record in self:
            record.cheque_end_series = record.start_series + record.leaf_count

    # @api.depends('start_series')
    # def _compute_cheque_start_series(self):
    #     for record in self:
    #         record.cheque_start_series = record.start_series + 1

    def print_generate_cheque(self):
        generated_numbers = []
        zero_padding = self.zero_padding

        for i in range(self.leaf_count):
            generated_numbers.append(self.start_series + i)

        record_vals = {
            'name':"{:0>{width}}".format(self.start_series, width=zero_padding + len(str(self.start_series))),
            'journal_id': self.journal_id.id,
        }
        record = self.env['cheque.leaf'].sudo().create(record_vals)

        line_vals = []
        for number in generated_numbers:
            line_vals.append((0, 0, {
                'name': "{:0>{width}}".format(number, width=zero_padding + len(str(number))),
                'status': 'draft',
            }))

        record.write({'cheque_leaf_line_ids': line_vals})

        return {
            'name': 'Cheque Leaf',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'cheque.leaf',
            'res_id': record.id,
            'target': 'current',
        }

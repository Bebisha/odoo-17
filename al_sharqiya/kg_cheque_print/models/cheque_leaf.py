from odoo import models, fields, api, _


class ChequeLeaf(models.Model):
    _name = 'cheque.leaf'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cheque Leaf'

    name = fields.Char("Cheque Series")
    cheque_series = fields.Char(string="Cheque Series")
    journal_id = fields.Many2one('account.journal', string="Journal")
    cheque_leaf_line_ids = fields.One2many('cheque.leaf.line', 'cheque_leaf_line_id', string="Leaf Line",
                                           ondelete='cascade')
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('confirm', "Confirm"),
            ("deactivate", "Deactivate")
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        default='draft')
    company_id = fields.Many2one(related='journal_id.company_id')

    def action_cheque_leaf_confirm(self):
        self.state = 'confirm'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('cheque.leaf') or _('New')
        return super(ChequeLeaf, self).create(vals)

    def action_deactivate(self):
        for rec in self:
            rec.state = 'deactivate'
            for line in rec.cheque_leaf_line_ids:
                line.status = 'deactivate'
            # rec.write({
            #     'state': "deactivate"
            # })


class ChequeLeafLine(models.Model):
    _name = 'cheque.leaf.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Cheque Leaf Line'

    cheque_leaf_line_id = fields.Many2one('cheque.leaf', string="Cheque Leaf Line")
    journal_id = fields.Many2one('account.journal', string="Journal", related="cheque_leaf_line_id.journal_id")
    name = fields.Char(string="Cheque Number")
    status = fields.Selection(
        [('draft', 'Open'), ('issued', 'Issued'), ('cancel', 'Cancel'), ('hold', 'Hold'), ('deactivate', 'Deactivate')],
        default='draft', string="Status")
    account_payment_id = fields.Many2one('account.payment', string="Payment")

    # cheque_series = fields.Char(string="Cheque Series", related='cheque_leaf_line_id.cheque_series', store=True)
    # name = fields.Char(string="Name", related='cheque_leaf_line_id.name', store=True)

    def hold_cheque_leaf(self):
        for rec in self:
            rec.write({'status': 'hold'})


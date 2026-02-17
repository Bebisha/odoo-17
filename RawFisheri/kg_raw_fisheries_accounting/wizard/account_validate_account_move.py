from odoo import models,_
from odoo.exceptions import UserError


class KGAccountValidateInherit(models.TransientModel):
    _inherit = "validate.account.move"

    def validate_move(self):
        if self._context.get('active_model') == 'account.move':
            domain = [('id', 'in', self._context.get('active_ids', [])), ('state', 'in', ['draft','approved'])]
        elif self._context.get('active_model') == 'account.journal':
            domain = [('journal_id', '=', self._context.get('active_id')), ('state', '=', 'draft')]
        else:
            raise UserError(_("Missing 'active_model' in context."))

        moves = self.env['account.move'].search(domain).filtered('line_ids')
        if not moves:
            raise UserError(_('There are no journal items in the draft state to post.'))
        if self.force_post:
            moves.auto_post = 'no'
        # try:
        moves._post(not self.force_post)
        # except TaxClosingNonPostedDependingMovesError as exception:
        #     return {
        #         "type": "ir.actions.client",
        #         "tag": "account_reports.redirect_action",
        #         "target": "new",
        #         "name": "Depending Action",
        #         "params": {
        #             "depending_action": exception.args[0],
        #         },
        #         'context': {
        #             'dialog_size': 'medium',
        #         },
        #     }
        return {'type': 'ir.actions.act_window_close'}

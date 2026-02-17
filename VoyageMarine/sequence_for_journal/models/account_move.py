from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_starting_sequence(self):
        self.ensure_one()
        seq_year = self.date.strftime('%y')
        seq_month = self.date.strftime('%m')
        seq_year_date = f"{seq_year}{seq_month}"
        starting_sequence = "%s/%s/00" % (self.journal_id.code, seq_year_date)
        if self.journal_id.refund_sequence and self.move_type in ('out_refund', 'in_refund'):
            starting_sequence = "R" + starting_sequence
        if self.journal_id.payment_sequence and self.payment_id:
            starting_sequence = "P" + starting_sequence
        return starting_sequence

    def _set_next_sequence(self):
        self.ensure_one()
        seq_year = self.date.strftime('%y')
        seq_month = self.date.strftime('%m')
        seq_year_date = f"{seq_year}{seq_month}"
        last_sequence = self._get_last_sequence()
        new = not last_sequence
        if new:
            last_sequence = self._get_last_sequence(relaxed=True) or \
                            self._get_starting_sequence()

        format, format_values = self._get_sequence_format_param(last_sequence)
        if new:
            format_values['seq'] = 0
        if self.journal_id.sequence_id.number_increment > 0:
            interpolated_prefix, interpolated_suffix = self.journal_id.sequence_id._get_prefix_suffix()
            format_values['seq'] = format_values['seq'] + self.journal_id.sequence_id.number_increment
            if self.journal_id.refund_sequence and self.move_type in ('out_refund', 'in_refund'):
                interpolated_prefix = "R" + interpolated_prefix
            if self.journal_id.payment_sequence and self.payment_id and self.payment_id.payment_type == 'inbound':
                interpolated_prefix = "R" + interpolated_prefix
            if self.journal_id.payment_sequence and self.payment_id and self.payment_id.payment_type == 'outbound':
                interpolated_prefix = "P" + interpolated_prefix
            format_values['prefix1'] = interpolated_prefix + "/" + seq_year_date + "/"
            if self.journal_id.sequence_id.suffix:
                format_values['suffix'] = "/" + interpolated_suffix
            else:
                format_values['suffix'] = ""
        else:
            format_values['prefix1'] = self.journal_id.code + "/" + seq_year_date + "/"
            format_values['seq'] = format_values['seq'] + self.journal_id.default_step_size
        self[self._sequence_field] = format.format(**format_values)
        self._compute_split_sequence()

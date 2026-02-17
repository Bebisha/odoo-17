from odoo import models, fields, _


class KGPartnerDocuments(models.Model):
    _inherit = "res.partner"

    document_count = fields.Integer(compute='compute_document_count',
                                    string='# Documents')

    def compute_document_count(self):
        for each in self:
            document_ids = self.env['hr.employee.document'].sudo().search(
                [('partner_id', '=', each.id)])
            each.document_count = len(document_ids)

    def document_view(self):
        self.ensure_one()
        domain = [
            ('partner_id', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'hr.employee.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="oe_view_nocontent_create">
                                 Click to Create for New Documents
                              </p>'''),
            'limit': 80,
            'context': "{'default_partner_id': %s}" % self.id
        }


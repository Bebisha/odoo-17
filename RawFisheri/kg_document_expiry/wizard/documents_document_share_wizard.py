# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class DocumentsDocumentShareWizard(models.TransientModel):
    """ Model: To share the document with specific users. """
    _name = 'documents.document.share.wizard'
    _description = 'documents.document.share.wizard'

    document_id = fields.Many2many('documents.document', string='Shared Documents', readonly=True)
    document_user_ids = fields.Many2many('res.users', string='Users to Share With', copy=False, required=False)
    remove_document_id = fields.Many2one('documents.document', string='Document to Update', readonly=False)
    remove_user_ids = fields.Many2many('res.users', 'user_id', string='Users to Remove Access From', copy=False,
                                       required=False, readonly=False)
    is_remove = fields.Boolean(string='Remove Shared Access', default=False)

    @api.onchange('remove_document_id')
    def _onchange_remove_document_id(self):
        """ Onchange of remove_document_id to load the corresponding shared users. """
        users = self.remove_document_id.mapped('document_user_ids').ids
        self.write({'remove_user_ids': [fields.Command.link(user) for user in users]})

    def action_confirm(self):
        """ function action confirm to assign the shared users to the document. """
        if self.document_user_ids and self.remove_user_ids:
            raise ValidationError("You cannot share and remove users at the same time.")
        if self.is_remove and self.remove_document_id:
            users_to_remove = self.remove_user_ids.ids
            updated_user_ids = [user for user in self.remove_document_id.document_user_ids.ids if
                                user in users_to_remove]
            self.remove_document_id.write({'document_user_ids': [fields.Command.set(updated_user_ids)]})
        users = self.mapped('document_user_ids').ids
        for document in self.document_id:
            document.write({'document_user_ids': [fields.Command.link(user) for user in users]})

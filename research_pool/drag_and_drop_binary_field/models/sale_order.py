# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Shonima(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, api
from odoo import api, fields, models
import requests
import logging
import base64

from odoo.exceptions import UserError
from odoo.http import request


class SaleOrder(models.Model):
    """Inherited sale. order class to add a new field for attachments"""
    _inherit = 'sale.order'


    create_image_drop= fields.Binary(string="PDfffffffffffffff", readonly=False, store=True)
    file_name= fields.Char(string="PDfffffffffffffff")

    # @api.model
    # def create(self, vals):
    #     print(vals, 'vals')
    #     # for rec in self:
    #     attached_id = self.env['ir.attachment'].search([('name', '=', self.name)])
    #     # Ensure binary data is base64 encoded
    #     if 'create_image_drop' in vals and vals['create_image_drop']:
    #         print(vals, 'vals')
    #         print(vals['create_image_drop'],'jjjjjjjjjjjjjjjjjjjj')
    #
    #
    #     return super(SaleOrder, self).create(vals)
    # #
    # def write(self, vals):
    #     # Handle binary data updates
    #     if 'create_image_drop' in vals and vals['create_image_drop']:
    #         print(vals,'vals')
    #
    #         for record in self:
    #             attached_id = self.env['ir.attachment'].search([('name', '=', record.name)])
    #             attachment = self.env['ir.attachment'].search([
    #                 ('res_model', '=', 'sale.order'),
    #                 ('res_id', '=', record.id),
    #                 ('name', '=', 'create_image_drop')
    #             ])
    #             for attachments in attachment:
    #                 attachment_data = base64.b64encode(attachments.datas).decode('utf-8')
    #
    #                 self.env['ir.attachment'].create({
    #                     'name': record.name,
    #                     'type': 'binary',
    #                     'datas': attachment_data,
    #                     'res_model': 'sale.order',
    #                     'res_id': record.order_id.id,
    #                 })
    #
    #
    #                 if attachments:
    #                     attachment.write({'datas': vals['create_image_drop']})
    #                 else:
    #                     attachment_name = 'create_image_drop'
    #                     self._create_attachment(vals['create_image_drop'], attachment_name)
    #     return super(SaleOrder, self).write(vals)
    #
    # def _create_attachment(self, binary_data, name):
    #     print('binary_data',binary_data)
    #     attachment_vals = {
    #         'name': name,
    #         'type': 'binary',
    #         'datas': binary_data,  # Expect base64-encoded data here
    #         'res_model': 'sale.order',
    #         'res_id': self.id,
    #     }
    #     print('attachment_vals',attachment_vals)
    #     attachment = self.env['ir.attachment'].create(attachment_vals)
    #     print(attachment,'attachment')
    #     return attachment.id

    @api.model
    def get_file_info(self, record_id, create_image_drop):
        print("Record ID Passed:", record_id)

        record = self.browse(record_id)
        if not record:
            print("No record found for the given ID.")
            return {}

        print("Record:", record)

        # Search for the attachments linked to this sale order
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', record_id)
        ])

        print("Attachments Found:", attachments)

        if not attachments:
            print("No attachments found for this sale order.")
            return {}

        # Iterate through the attachments to find the one with the same file content
        for attachment in attachments:
            print(f"Checking Attachment Name: {attachment.name}")
            print(f"Checking attachment.datas: {attachment.datas}")
            # Assuming you can access file content from the binary field for comparison
            if attachment.datas == record.create_image_drop:
                print(f"Found Matching Attachment: {attachment.name}")
                file_info = {
                    'fileId': attachment.id,
                    'fileType': attachment.mimetype,
                    'fileName': attachment.name,
                    'fileUrl': f'/web/content/{attachment.id}?download=true',
                }

                print("File Info:", file_info)
                return file_info

        # If no matching attachment was found
        print("No matching attachment found for the provided binary data.")
        return {"error": "No matching attachment found for the provided binary data."}

    attachment_drop_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string="Attachmentsiii", help="Add Multiple attachment file",relation='drop')


    #
    #
    # @api.depends("attachment_urls")
    # def _compute_image(self):
    #     for record in self:
    #         image = None
    #         if record.attachment_urls:
    #             image = self.get_image_from_url(record.attachment_urls)
    #             self.check_access_rule(image)
    #         record.update({"create_image": image, })

    # def action_preview_image(self):
    #     self.ensure_one()
    #     if self.create_image:
    #         return {
    #             'type': 'ir.actions.act_url',
    #             'url': '/web/image/%s/create_image' % self.id,
    #             'target': 'new',
    #         }
    #     else:
    #         return {
    #             'type': 'ir.actions.act_window_message',
    #             'title': 'No Image',
    #             'message': 'No image found to preview.',
    #             'button_text': 'Close',
    #         }
    #
    # @api.model
    # def get_image_url(self, record_id):
    #     record = self.browse(record_id)
    #     if record.create_image:
    #         return '/web/image/%s/create_image' % record_id
    #     return None

    name = fields.Char('File Name')
    file_data = fields.Binary('File Data')
    file_type = fields.Char('File Type')

    @api.model
    def upload_file(self, file_data, file_name):
        if not file_data:
            raise UserError("No file data provided.")
        existing_record = self.search([('name', '=', file_name)], limit=1)
        if existing_record:
            existing_record.write({
                'file_data': file_data,
                'file_type': self._get_file_type(file_data),
            })
            return existing_record.id
        else:
            return self.create({
                'file_data': file_data,
                'name': file_name,
                'file_type': self._get_file_type(file_data),
            }).id

    def _get_file_type(self, file_data):
        import mimetypes
        import base64
        file_type, _ = mimetypes.guess_type(base64.b64decode(file_data).decode('utf-8', 'ignore'))
        return file_type or 'application/octet-stream'
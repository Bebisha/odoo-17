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
from odoo import models, api, _, fields
from collections import defaultdict
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class ImageFromURLMixin:
    def get_image_from_url(self, url):
        """
        :return: Returns a base64 encoded string.
        """
        data = ""
        try:
            # Python 2
            # data = requests.get(url.strip()).content.encode("base64").replace("\n", "")
            # Python 3
            data = base64.b64encode(requests.get(url.strip()).content).replace(b"\n", b"")
        except Exception as e:
            _logger.warning("Can't load the image from URL %s" % url)
            logging.exception(e)
        return data



class SaleOrder(models.Model):
    """Inherited sale. order class to add a new field for attachments"""
    _inherit = 'sale.order'

    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string="Attachments", help="Add Multiple attachment file")

    username_char = fields.Char()


    #
    # attachment_urls = fields.Char(
    #     string="Attachment URLs",
    #     compute='_compute_attachment_urls',
    #     store=True,
    #     help="Comma-separated URLs of the attachments"
    # )
    # create_image = fields.Binary(string="Image", compute='_compute_image', readonly=False, store=True)
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
    #
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

class IrAttachment(models.Model):
    _inherit = "res.partner"

    attachment_ids = fields.Many2many('ir.attachment',string="attachments")

